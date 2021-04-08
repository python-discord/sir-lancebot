import logging
import random
import re
import typing as t
from dataclasses import dataclass

import discord
from discord.ext import commands, tasks

from bot.constants import (
    Categories,
    Channels,
    Colours,
    ERROR_REPLIES,
    Emojis,
    NEGATIVE_REPLIES,
    Tokens,
    WHITELISTED_CHANNELS
)
from bot.utils.decorators import whitelist_override
from bot.utils.extensions import invoke_help_command

log = logging.getLogger(__name__)

BAD_RESPONSE = {
    404: "Issue/pull request not located! Please enter a valid number!",
    403: "Rate limit has been hit! Please try again later!"
}
REQUEST_HEADERS = {
    "Accept": "application/vnd.github.v3+json"
}

REPOSITORY_ENDPOINT = "https://api.github.com/orgs/{org}/repos"
ISSUE_ENDPOINT = "https://api.github.com/repos/{user}/{repository}/issues/{number}"
PR_MERGE_ENDPOINT = "https://api.github.com/repos/{user}/{repository}/pulls/{number}/merge"

if GITHUB_TOKEN := Tokens.github:
    REQUEST_HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

WHITELISTED_CATEGORIES = (
    Categories.development, Categories.devprojects, Categories.media, Categories.staff
)

CODE_BLOCK_RE = re.compile(
    r"^`([^`\n]+)`"  # Inline codeblock
    r"|```(.+?)```",  # Multiline codeblock
    re.DOTALL | re.MULTILINE
)

# Maximum number of issues in one message
MAXIMUM_ISSUES = 5


@dataclass
class FetchError:
    """Dataclass representing an error while fetching an issue."""

    return_code: int
    message: str


@dataclass
class IssueState:
    """Dataclass representing the state of an issue."""

    repository: str
    number: int
    url: str
    title: str
    icon_url: str


class Issues(commands.Cog):
    """Cog that allows users to retrieve issues from GitHub."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.repos = []
        self.repo_regex = None
        self.get_pydis_repos.start()

    @tasks.loop(minutes=30)
    async def get_pydis_repos(self) -> None:
        """
        Get all python-discord repositories on github.

        This task will update a pipe-separated list of repositories in self.repo_regex.
        """
        async with self.bot.http_session.get(
                REPOSITORY_ENDPOINT.format(org="python-discord"),
                headers=REQUEST_HEADERS
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                for repo in data:
                    self.repos.append(repo["full_name"].split("/")[1])
                self.repo_regex = "|".join(self.repos)
            else:
                log.warning(f"Failed to get latest Pydis repositories. Status code {resp.status}")

    @staticmethod
    def check_in_block(message: discord.Message, repo_issue: str) -> bool:
        """Check whether the <repo>#<issue> is in codeblocks."""
        block = re.findall(CODE_BLOCK_RE, message.content)

        if not block:
            return False
        elif "#".join(repo_issue.split(" ")) in "".join([*block[0]]):
            return True
        return False

    async def fetch_issues(
            self,
            number: int,
            repository: str,
            user: str
    ) -> t.Union[IssueState, FetchError]:
        """
        Retrieve an issue from a GitHub repository.

        Returns IssueState on success, FetchError on failure.
        """
        url = ISSUE_ENDPOINT.format(user=user, repository=repository, number=number)
        merge_url = PR_MERGE_ENDPOINT.format(user=user, repository=repository, number=number)
        log.trace(f"Querying GH issues API: {url}")

        async with self.bot.http_session.get(url, headers=REQUEST_HEADERS) as r:
            json_data = await r.json()

        if r.status == 403:
            if r.headers.get("X-RateLimit-Remaining") == "0":
                log.info(f"Ratelimit reached while fetching {url}")
                return FetchError(403, "Ratelimit reached, please retry in a few minutes.")
            return FetchError(403, "Cannot access issue.")
        elif r.status in (404, 410):
            return FetchError(r.status, "Issue not found.")
        elif r.status != 200:
            return FetchError(r.status, "Error while fetching issue.")

        # The initial API request is made to the issues API endpoint, which will return information
        # if the issue or PR is present. However, the scope of information returned for PRs differs
        # from issues: if the 'issues' key is present in the response then we can pull the data we
        # need from the initial API call.
        if "issues" in json_data["html_url"]:
            if json_data.get("state") == "open":
                icon_url = Emojis.issue
            else:
                icon_url = Emojis.issue_closed

        # If the 'issues' key is not contained in the API response and there is no error code, then
        # we know that a PR has been requested and a call to the pulls API endpoint is necessary
        # to get the desired information for the PR.
        else:
            log.trace(f"PR provided, querying GH pulls API for additional information: {merge_url}")
            async with self.bot.http_session.get(merge_url) as m:
                if json_data.get("state") == "open":
                    icon_url = Emojis.pull_request
                # When the status is 204 this means that the state of the PR is merged
                elif m.status == 204:
                    icon_url = Emojis.merge
                else:
                    icon_url = Emojis.pull_request_closed

        issue_url = json_data.get("html_url")

        return IssueState(repository, number, issue_url, json_data.get('title', ''), icon_url)

    @staticmethod
    def format_embed(
            results: t.List[t.Union[IssueState, FetchError]],
            user: str,
            repository: t.Optional[str] = None
    ) -> discord.Embed:
        """Take a list of IssueState or FetchError and format a Discord embed for them."""
        description_list = []

        for result in results:
            if isinstance(result, IssueState):
                description_list.append(f"{result.icon_url} [{result.title}]({result.url})")
            elif isinstance(result, FetchError):
                description_list.append(f"[{result.return_code}] {result.message}")

        resp = discord.Embed(
            colour=Colours.bright_green,
            description='\n'.join(description_list)
        )

        embed_url = f"https://github.com/{user}/{repository}" if repository else f"https://github.com/{user}"
        resp.set_author(name="GitHub", url=embed_url)
        return resp

    @whitelist_override(channels=WHITELISTED_CHANNELS, categories=WHITELISTED_CATEGORIES)
    @commands.command(aliases=("pr",))
    async def issue(
            self,
            ctx: commands.Context,
            numbers: commands.Greedy[int],
            repository: str = "sir-lancebot",
            user: str = "python-discord"
    ) -> None:
        """Command to retrieve issue(s) from a GitHub repository."""
        # Remove duplicates
        numbers = set(numbers)

        if len(numbers) > MAXIMUM_ISSUES:
            embed = discord.Embed(
                title=random.choice(ERROR_REPLIES),
                color=Colours.soft_red,
                description=f"Too many issues/PRs! (maximum of {MAXIMUM_ISSUES})"
            )
            await ctx.send(embed=embed)
            await invoke_help_command(ctx)

        results = [await self.fetch_issues(number, repository, user) for number in numbers]
        await ctx.send(embed=self.format_embed(results, user, repository))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Command to retrieve issue(s) from a GitHub repository using automatic linking if matching <repo>#<issue>."""
        if not self.repo_regex:
            log.warning("repo_regex isn't ready, cannot look for issues.")
            return

        # Ignore bots
        if message.author.bot:
            return

        # `issues` will hold a list of two element tuples `(repository, issue_number)`
        issues = re.findall(fr"({self.repo_regex})#(\d+)", message.content)
        links = []

        if issues:
            # Block this from working in DMs
            if not message.guild:
                await message.channel.send(
                    embed=discord.Embed(
                        title=random.choice(NEGATIVE_REPLIES),
                        description=(
                            "You can't retrieve issues from DMs. "
                            f"Try again in <#{Channels.community_bot_commands}>"
                        ),
                        colour=discord.Colour.red()
                    )
                )
                return

            log.trace(f"Found {issues = }")
            # Remove duplicates
            issues = set(issues)

            if len(issues) > MAXIMUM_ISSUES:
                embed = discord.Embed(
                    title=random.choice(ERROR_REPLIES),
                    color=Colours.soft_red,
                    description=f"Too many issues/PRs! (maximum of {MAXIMUM_ISSUES})"
                )
                await message.channel.send(embed=embed, delete_after=5)
                return

            for repo_issue in issues:
                if not self.check_in_block(message, " ".join(repo_issue)):
                    result = await self.fetch_issues(repo_issue[1], repo_issue[0], "python-discord")
                    if isinstance(result, IssueState):
                        links.append(result)

        if not links:
            return

        resp = self.format_embed(links, "python-discord")
        await message.channel.send(embed=resp)


def setup(bot: commands.Bot) -> None:
    """Cog Retrieves Issues From Github."""
    bot.add_cog(Issues(bot))

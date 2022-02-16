import logging
import random
import re
from dataclasses import dataclass
from typing import Optional, Union

import discord
from discord.ext import commands

from bot.bot import Bot
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

REPOSITORY_ENDPOINT = "https://api.github.com/orgs/{org}/repos?per_page=100&type=public"
ISSUE_ENDPOINT = "https://api.github.com/repos/{user}/{repository}/issues/{number}"
PR_ENDPOINT = "https://api.github.com/repos/{user}/{repository}/pulls/{number}"

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

# Regex used when looking for automatic linking in messages
# regex101 of current regex https://regex101.com/r/V2ji8M/6
AUTOMATIC_REGEX = re.compile(
    r"((?P<org>[a-zA-Z0-9][a-zA-Z0-9\-]{1,39})\/)?(?P<repo>[\w\-\.]{1,100})#(?P<number>[0-9]+)"
)


@dataclass
class FoundIssue:
    """Dataclass representing an issue found by the regex."""

    organisation: Optional[str]
    repository: str
    number: str

    def __hash__(self) -> int:
        return hash((self.organisation, self.repository, self.number))


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
    emoji: str


class Issues(commands.Cog):
    """Cog that allows users to retrieve issues from GitHub."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.repos = []

    @staticmethod
    def remove_codeblocks(message: str) -> str:
        """Remove any codeblock in a message."""
        return re.sub(CODE_BLOCK_RE, "", message)

    async def fetch_issues(
            self,
            number: int,
            repository: str,
            user: str
    ) -> Union[IssueState, FetchError]:
        """
        Retrieve an issue from a GitHub repository.

        Returns IssueState on success, FetchError on failure.
        """
        url = ISSUE_ENDPOINT.format(user=user, repository=repository, number=number)
        pulls_url = PR_ENDPOINT.format(user=user, repository=repository, number=number)
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
                emoji = Emojis.issue_open
            else:
                emoji = Emojis.issue_closed

        # If the 'issues' key is not contained in the API response and there is no error code, then
        # we know that a PR has been requested and a call to the pulls API endpoint is necessary
        # to get the desired information for the PR.
        else:
            log.trace(f"PR provided, querying GH pulls API for additional information: {pulls_url}")
            async with self.bot.http_session.get(pulls_url) as p:
                pull_data = await p.json()
                if pull_data["draft"]:
                    emoji = Emojis.pull_request_draft
                elif pull_data["state"] == "open":
                    emoji = Emojis.pull_request_open
                # When 'merged_at' is not None, this means that the state of the PR is merged
                elif pull_data["merged_at"] is not None:
                    emoji = Emojis.pull_request_merged
                else:
                    emoji = Emojis.pull_request_closed

        issue_url = json_data.get("html_url")

        return IssueState(repository, number, issue_url, json_data.get("title", ""), emoji)

    @staticmethod
    def format_embed(
        results: list[Union[IssueState, FetchError]],
        user: str,
        repository: Optional[str] = None
    ) -> discord.Embed:
        """Take a list of IssueState or FetchError and format a Discord embed for them."""
        description_list = []

        for result in results:
            if isinstance(result, IssueState):
                description_list.append(f"{result.emoji} [{result.title}]({result.url})")
            elif isinstance(result, FetchError):
                description_list.append(f":x: [{result.return_code}] {result.message}")

        resp = discord.Embed(
            colour=Colours.bright_green,
            description="\n".join(description_list)
        )

        embed_url = f"https://github.com/{user}/{repository}" if repository else f"https://github.com/{user}"
        resp.set_author(name="GitHub", url=embed_url)
        return resp

    @whitelist_override(channels=WHITELISTED_CHANNELS, categories=WHITELISTED_CATEGORIES)
    @commands.command(aliases=("issues", "pr", "prs"))
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

        err_message = None
        if not numbers:
            err_message = "You must have at least one issue/PR!"

        elif len(numbers) > MAXIMUM_ISSUES:
            err_message = f"Too many issues/PRs! (maximum of {MAXIMUM_ISSUES})"

        # If there's an error with command invocation then send an error embed
        if err_message is not None:
            err_embed = discord.Embed(
                title=random.choice(ERROR_REPLIES),
                color=Colours.soft_red,
                description=err_message
            )
            await ctx.send(embed=err_embed)
            await invoke_help_command(ctx)
            return

        results = [await self.fetch_issues(number, repository, user) for number in numbers]
        await ctx.send(embed=self.format_embed(results, user, repository))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Automatic issue linking.

        Listener to retrieve issue(s) from a GitHub repository using automatic linking if matching <org>/<repo>#<issue>.
        """
        # Ignore bots
        if message.author.bot:
            return

        issues = [
            FoundIssue(*match.group("org", "repo", "number"))
            for match in AUTOMATIC_REGEX.finditer(self.remove_codeblocks(message.content))
        ]
        links = []

        if issues:
            # Block this from working in DMs
            if not message.guild:
                await message.channel.send(
                    embed=discord.Embed(
                        title=random.choice(NEGATIVE_REPLIES),
                        description=(
                            "You can't retrieve issues from DMs. "
                            f"Try again in <#{Channels.sir_lancebot_playground}>"
                        ),
                        colour=Colours.soft_red
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
                result = await self.fetch_issues(
                    int(repo_issue.number),
                    repo_issue.repository,
                    repo_issue.organisation or "python-discord"
                )
                if isinstance(result, IssueState):
                    links.append(result)

        if not links:
            return

        resp = self.format_embed(links, "python-discord")
        await message.channel.send(embed=resp)


def setup(bot: Bot) -> None:
    """Load the Issues cog."""
    bot.add_cog(Issues(bot))

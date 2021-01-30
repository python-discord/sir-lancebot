import logging
import random
import re
import typing as t
from enum import Enum

import discord
from discord.ext import commands, tasks

from bot.constants import Categories, Channels, Colours, ERROR_REPLIES, Emojis, Tokens, WHITELISTED_CHANNELS

log = logging.getLogger(__name__)

BAD_RESPONSE = {
    404: "Issue/pull request not located! Please enter a valid number!",
    403: "Rate limit has been hit! Please try again later!"
}

MAX_REQUESTS = 10
REQUEST_HEADERS = dict()

REPOS_API = "https://api.github.com/orgs/{org}/repos"
if GITHUB_TOKEN := Tokens.github:
    REQUEST_HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

WHITELISTED_CATEGORIES = (
    Categories.devprojects, Categories.media, Categories.development
)
WHITELISTED_CHANNELS_ON_MESSAGE = (Channels.organisation,)

CODE_BLOCK_RE = re.compile(
    r"^`([^`\n]+)`"  # Inline codeblock
    r"|```(.+?)```",  # Multiline codeblock
    re.DOTALL | re.MULTILINE
)


class FetchIssueErrors(Enum):
    """Errors returned in fetch issues."""

    value_error = "Numbers not found."
    max_requests = "Max requests hit."


class Issues(commands.Cog):
    """Cog that allows users to retrieve issues from GitHub."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.repos = []
        self.get_pydis_repos.start()

    @tasks.loop(minutes=30)
    async def get_pydis_repos(self) -> None:
        """Get all python-discord repositories on github."""
        async with self.bot.http_session.get(REPOS_API.format(org="python-discord")) as resp:
            if resp.status == 200:
                data = await resp.json()
                for repo in data:
                    self.repos.append(repo["full_name"].split("/")[1])
                self.repo_regex = "|".join(self.repos)
            else:
                log.debug(f"Failed to get latest Pydis repositories. Status code {resp.status}")

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
            numbers: set,
            repository: str,
            user: str
    ) -> t.Union[FetchIssueErrors, str, list]:
        """Retrieve issue(s) from a GitHub repository."""
        links = []
        if not numbers:
            return FetchIssueErrors.value_error

        if len(numbers) > MAX_REQUESTS:
            return FetchIssueErrors.max_requests

        for number in numbers:
            url = f"https://api.github.com/repos/{user}/{repository}/issues/{number}"
            merge_url = f"https://api.github.com/repos/{user}/{repository}/pulls/{number}/merge"
            log.trace(f"Querying GH issues API: {url}")
            async with self.bot.http_session.get(url, headers=REQUEST_HEADERS) as r:
                json_data = await r.json()

            if r.status in BAD_RESPONSE:
                log.warning(f"Received response {r.status} from: {url}")
                return f"[{str(r.status)}] #{number} {BAD_RESPONSE.get(r.status)}"

            # The initial API request is made to the issues API endpoint, which will return information
            # if the issue or PR is present. However, the scope of information returned for PRs differs
            # from issues: if the 'issues' key is present in the response then we can pull the data we
            # need from the initial API call.
            if "issues" in json_data.get("html_url"):
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
            links.append([icon_url, f"[{repository}] #{number} {json_data.get('title')}", issue_url])

        return links

    @staticmethod
    def get_embed(result: list, user: str = "python-discord", repository: str = "") -> discord.Embed:
        """Get Response Embed."""
        description_list = ["{0} [{1}]({2})".format(*link) for link in result]
        resp = discord.Embed(
            colour=Colours.bright_green,
            description='\n'.join(description_list)
        )

        resp.set_author(name="GitHub", url=f"https://github.com/{user}/{repository}")
        return resp

    @commands.command(aliases=("pr",))
    async def issue(
            self,
            ctx: commands.Context,
            numbers: commands.Greedy[int],
            repository: str = "sir-lancebot",
            user: str = "python-discord"
    ) -> None:
        """Command to retrieve issue(s) from a GitHub repository."""
        if not(
            ctx.channel.category.id in WHITELISTED_CATEGORIES
            or ctx.channel.id in WHITELISTED_CHANNELS
        ):
            return

        result = await self.fetch_issues(set(numbers), repository, user)

        if result == FetchIssueErrors.value_error:
            await ctx.invoke(self.bot.get_command('help'), 'issue')

        elif result == FetchIssueErrors.max_requests:
            embed = discord.Embed(
                title=random.choice(ERROR_REPLIES),
                color=Colours.soft_red,
                description=f"Too many issues/PRs! (maximum of {MAX_REQUESTS})"
            )
            await ctx.send(embed=embed)

        elif isinstance(result, list):
            # Issue/PR format: emoji to show if open/closed/merged, number and the title as a singular link.
            resp = self.get_embed(result, user, repository)
            await ctx.send(embed=resp)

        elif isinstance(result, str):
            await ctx.send(result)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Command to retrieve issue(s) from a GitHub repository using automatic linking if matching <repo>#<issue>."""
        if not(
            message.channel.category.id in WHITELISTED_CATEGORIES
            or message.channel.id in WHITELISTED_CHANNELS_ON_MESSAGE
        ):
            return

        message_repo_issue_map = re.findall(fr".+?({self.repo_regex})#(\d+)", message.content)
        links = []

        if message_repo_issue_map:
            for repo_issue in message_repo_issue_map:
                if not self.check_in_block(message, " ".join([*repo_issue])):
                    result = await self.fetch_issues({repo_issue[1]}, repo_issue[0], "python-discord")
                    if isinstance(result, list):
                        links.extend(result)

        if not links:
            return

        resp = self.get_embed(links, "python-discord")
        await message.channel.send(embed=resp)


def setup(bot: commands.Bot) -> None:
    """Cog Retrieves Issues From Github."""
    bot.add_cog(Issues(bot))

import re

from discord.ext.commands import Cog, Context, command

from bot.bot import Bot
from bot.constants import Tokens


class GetCommits(Cog):
    """Example Class used for testing."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot


    @command(name="get-commits")
    async def github_commits(self, ctx: Context, start_str: str, end_str: str, repo_str: str) -> None:
        """Hot dogs."""
        count = await self.get_commit_count(repo_str, start_str, end_str)

        count_message = (
            f"Commit count for **{repo_str}** between **{start_str}** and **{end_str}** is **{count}**"
        )

        await ctx.send(count_message)


    # GitHub API for commits:
    # https://docs.github.com/en/rest/commits/commits?apiVersion=2022-11-28#list-commits
    #
    # When we get to this stage in the command, we already know that:
    # repo_str, start_str and end_str are formatted correctly. We also know that the repo exists so all we need
    # to do is to make the API call.
    async def get_commit_count(self, repo_str: str, start_str: str, end_str: str) -> int:
        """
        Returns the number of commits done to the given repo between the start- and end-date.

        Args:
            repo_str: The repository string in the format "owner/repo.
            start_str: The start date of the interval.
            end_str: The end date of the interval.
            page: The page number.
            per_page: The number of results per page in the request.
                Setting this to one and reading request.links will result in the number of pages = number of commits.
        """
        per_page = 1
        page = 1
        # Formatting in ISO8601 standard:
        # YYYY-MM-DDTHH:MM:SSZ
        start_iso = f"{start_str}T00:00:00Z"
        end_iso = f"{end_str}T23:59:59Z"

        header = {"Authorization": f"token {Tokens.github.get_secret_value()}"}

        url = (
            f"https://api.github.com/repos/{repo_str}/commits"
            f"?since={start_iso}&until={end_iso}&per_page={per_page}&page={page}"
        )

        async with self.bot.http_session.get(url, headers=header) as response:

            if response.status != 200:
                return -1

            commits_json = await response.json()
            # No commits
            if not commits_json:
                return 0

            link_header = response.headers.get("Link")
            # No link header means only one page
            if not link_header:
                return 1

            # Grabbing the number of pages from the Link header
            match = re.search(r'page=(\d+)>; rel="last"', link_header)

            if match:
                return int(match.group(1))

            return 1


async def setup(bot: Bot) -> None:
    """Very weird."""
    await bot.add_cog(GetCommits(bot))

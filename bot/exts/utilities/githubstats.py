from discord.ext.commands import Cog, Context, command

from bot.bot import Bot
from bot.constants import Tokens

GITHUB_API_URL = "https://api.github.com"


class GitHubStats(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @command(name="gh-stats")
    async def github_stats(self, ctx: Context, start: str, end: str, repo: str = "python-discord/sir-lancebot") -> None:
        """
        Fetches stats for a GitHub repo.
        Usage: !github_stats 2023-01-01 2023-12-31 python-discord/bot.
        """
        if not await self.repo_exists(repo):
            await ctx.send(f"Could not find repository: `{repo}`")
            return

        open = await self.get_issue_count(repo, start, end, state="created")
        closed = await self.get_issue_count(repo, start, end, state="closed")

        prs_opened = await self.get_pr_count(repo, start, end, "opened")
        prs_closed = await self.get_pr_count(repo, start, end, "closed")
        prs_merged = await self.get_pr_count(repo, start, end, "merged")

        stats_message = (
            f"Stats for **{repo}** ({start} to {end}):\n"
            f"Issues opened: {open}\n"
            f"Issues closed: {closed} \n"
            f"Pull Requests opened: {prs_opened} \n"
            f"Pull Requests closed: {prs_closed} \n"
            f"Pull Requests merged: {prs_merged} \n"
        )
        await ctx.send(stats_message)

    async def repo_exists(self, repo: str) -> bool:
        """
        Checks if a repository exists on GitHub.

        Args:
            repo (str): The repository name in 'owner/repo' format (e.g., 'python-discord/bot').
        """
        url = f"{GITHUB_API_URL}/repos/{repo}"
        headers = {"Authorization": f"token {Tokens.github.get_secret_value()}"}

        async with self.bot.http_session.get(url, headers=headers) as response:
            return response.status == 200

    async def get_issue_count(self, repo: str, start: str, end: str, state: str) -> int:
        """
        Gets the number of issues opened or closed (based on state) in a given timeframe.

        Args:
            repo (str): The repository name in 'owner/repo' format (e.g., 'python-discord/bot').
            start (str): The start date (e.g., 2023-01-01).
            end (str): The end date (e.g., 2023-12-31).
            state (str): The state of the issue (created/closed)
        """
        url = f"{GITHUB_API_URL}/search/issues"
        headers = {"Authorization": f"token {Tokens.github.get_secret_value()}"}

        # The query string uses GitHub's advanced search syntax
        # e.g., repo:python-discord/bot is:issue created:2023-01-01..2023-12-31
        query = f"repo:{repo} is:issue {state}:{start}..{end}"
        params = {"q": query}

        async with self.bot.http_session.get(url, headers=headers, params=params) as response:
            if response.status != 200:
                return -1

            data = await response.json()
            return data.get("total_count", 0)

    async def get_pr_count(self, repo: str, start: str, end: str, action: str) -> int:
        """Gets the number of PRs opened, closed or merged in a given timeframe."""
        url = f"{GITHUB_API_URL}/search/issues"
        headers = {"Authorization": f"token {Tokens.github.get_secret_value()}"}

        if action == "opened":
            state_query = f"created:{start}..{end}"
        elif action == "merged":
            state_query = f"is:merged merged:{start}..{end}"
        elif action == "closed":
            state_query = f"is:unmerged closed:{start}..{end}"
        else:
            return 0

        query = f"repo:{repo} is:pr {state_query}"
        params = {"q": query}

        async with self.bot.http_session.get(url, headers=headers, params=params) as response:
            if response.status != 200:
                return -1

            data = await response.json()
            return data.get("total_count", 0)


async def setup(bot: Bot) -> None:
    await bot.add_cog(GitHubStats(bot))

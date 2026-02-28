from discord.ext.commands import Cog, Context, command

from bot.bot import Bot
from math import ceil
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
        stars_gained = await self.get_stars_gained(repo, start, end)

        if stars_gained == -2:
            stars_gained_message = "N/A (repo exceeds API limit)"
        elif stars_gained > 0:
            stars_gained_message = f"+{stars_gained} ⭐"
        elif stars_gained == 0:
            stars_gained_message = "0 ⭐"
        else:
            stars_gained_message = "unavailable"
        
        stats_message = (
            f"Stats for **{repo}** ({start} to {end}):\n" f"Issues opened: {open}\n" f"Issues closed: {closed}\n" f"Stars gained: {stars_gained_message}\n"
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

    async def _fetch_page(self, url: str, headers: dict, page: int, cache: dict) -> list:
        """Fetch a page of stargazers, using cache to avoid duplicate requests.
        
        Args:
            url (str): The URL to fetch the page from.
            headers (dict): The headers to use for the request.
            page (int): The page number to fetch.
            cache (dict): The cache to use to avoid duplicate requests.
        """
        if page not in cache:
            async with self.bot.http_session.get(url, headers=headers, params={"per_page": 100, "page": page}) as response:
                if response.status != 200:
                    return []
                cache[page] = await response.json()
        return cache[page]

    async def _get_date_at(self, url: str, headers: dict, i: int, cache: dict) -> str:
        """Get the starred_at date (YYYY-MM-DD) of the star at global index i (0-based).
        Args:
            url (str): The URL to fetch the page from.
            headers (dict): The headers to use for the request.
            i (int): The global index of the star.
            cache (dict): The cache to use to avoid duplicate requests.

        """
        page = (i // 100) + 1
        pos = i % 100
        page_data = await self._fetch_page(url, headers, page, cache)
        # starred_at is in format YYYY-MM-DDTHH:MM:SSZ so we can just get the first 10 characters to get the date
        return page_data[pos].get("starred_at", "")[:10] if page_data else ""

    async def get_stars_gained(self, repo: str, start: str, end: str) -> int:
        """Gets the number of stars gained for a given repository in a timeframe.

        Args:
            repo (str): The repository name in 'owner/repo' format (e.g., 'python-discord/bot').
            start (str): The start date (e.g., 2023-01-01).
            end (str): The end date (e.g., 2023-12-31).
        """
        url = f"{GITHUB_API_URL}/repos/{repo}/stargazers"
        headers = {
            "Authorization": f"token {Tokens.github.get_secret_value()}",
            "Accept": "application/vnd.github.star+json",
        }

        async with self.bot.http_session.get(f"{GITHUB_API_URL}/repos/{repo}", headers={"Authorization": f"token {Tokens.github.get_secret_value()}"}) as response:
            if response.status != 200:
                return -1
            max_stars = (await response.json()).get("stargazers_count", 0)

        if max_stars == 0:
            return 0

        # GitHub API limits stargazers pagination to 40 000 entries (page 400 max)
        # Because of this the output is not consistent for projects with more than 40 000 stars so we default to -2
        GITHUB_STARGAZERS_LIMIT = 40000
        if max_stars > GITHUB_STARGAZERS_LIMIT:
            return -2
        searchable_stars = max_stars

        # We use a cache and binary search to limit the number of requests to the GitHub API
        cache = {}
        low, high = 0, searchable_stars - 1
        while low < high:
            mid = (low + high) // 2
            lowdate = await self._get_date_at(url, headers, mid, cache)
            if lowdate == "":
                return -1
            if lowdate < start:
                low = mid + 1
            else:
                high = mid
        left = low

        date_left = await self._get_date_at(url, headers, left, cache)
        if date_left < start or date_left > end:
            return 0

        low, high = left, searchable_stars - 1
        while low < high:
            mid = (low + high + 1) // 2
            highdate = await self._get_date_at(url, headers, mid, cache)
            if highdate == "":
                return -1
            if highdate > end:
                high = mid - 1
            else:
                low = mid
        right = low

        return right - left + 1
    
async def setup(bot: Bot) -> None:
    await bot.add_cog(GitHubStats(bot))

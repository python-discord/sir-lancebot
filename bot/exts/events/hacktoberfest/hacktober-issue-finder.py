import datetime
import logging
import random
from typing import Optional

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Month, Tokens
from bot.utils.decorators import in_month

log = logging.getLogger(__name__)

URL = "https://api.github.com/search/issues?per_page=100&q=is:issue+label:hacktoberfest+language:python+state:open"

REQUEST_HEADERS = {
    "User-Agent": "Python Discord Hacktoberbot",
    "Accept": "application / vnd.github.v3 + json"
}
if GITHUB_TOKEN := Tokens.github.get_secret_value():
    REQUEST_HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"


class HacktoberIssues(commands.Cog):
    """Find a random hacktober python issue on GitHub."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.cache_normal = None
        self.cache_timer_normal = datetime.datetime(1, 1, 1)
        self.cache_beginner = None
        self.cache_timer_beginner = datetime.datetime(1, 1, 1)

    @in_month(Month.OCTOBER)
    @commands.command()
    async def hacktoberissues(self, ctx: commands.Context, option: str = "") -> None:
        """
        Get a random python hacktober issue from Github.

        If the command is run with beginner (`.hacktoberissues beginner`):
        It will also narrow it down to the "first good issue" label.
        """
        async with ctx.typing():
            issues = await self.get_issues(ctx, option)
            if issues is None:
                return
            issue = random.choice(issues["items"])
            embed = self.format_embed(issue)
        await ctx.send(embed=embed)

    async def get_issues(self, ctx: commands.Context, option: str) -> Optional[dict]:
        """Get a list of the python issues with the label 'hacktoberfest' from the Github api."""
        if option == "beginner":
            if (ctx.message.created_at.replace(tzinfo=None) - self.cache_timer_beginner).seconds <= 60:
                log.debug("using cache")
                return self.cache_beginner
        elif (ctx.message.created_at.replace(tzinfo=None) - self.cache_timer_normal).seconds <= 60:
            log.debug("using cache")
            return self.cache_normal

        if option == "beginner":
            url = URL + '+label:"good first issue"'
            if self.cache_beginner is not None:
                page = random.randint(1, min(1000, self.cache_beginner["total_count"]) // 100)
                url += f"&page={page}"
        else:
            url = URL
            if self.cache_normal is not None:
                page = random.randint(1, min(1000, self.cache_normal["total_count"]) // 100)
                url += f"&page={page}"

        log.debug(f"making api request to url: {url}")
        async with self.bot.http_session.get(url, headers=REQUEST_HEADERS) as response:
            if response.status != 200:
                log.error(f"expected 200 status (got {response.status}) by the GitHub api.")
                await ctx.send(
                    f"ERROR: expected 200 status (got {response.status}) by the GitHub api.\n"
                    f"{await response.text()}"
                )
                return None
            data = await response.json()

            if len(data["items"]) == 0:
                log.error(f"no issues returned by GitHub API, with url: {response.url}")
                await ctx.send(f"ERROR: no issues returned by GitHub API, with url: {response.url}")
                return None

            if option == "beginner":
                self.cache_beginner = data
                self.cache_timer_beginner = ctx.message.created_at.replace(tzinfo=None)
            else:
                self.cache_normal = data
                self.cache_timer_normal = ctx.message.created_at.replace(tzinfo=None)

            return data

    @staticmethod
    def format_embed(issue: dict) -> discord.Embed:
        """Format the issue data into a embed."""
        title = issue["title"]
        issue_url = issue["url"].replace("api.", "").replace("/repos/", "/")
        # Issues can have empty bodies, resulting in the value being a literal `null` (parsed as `None`).
        # For this reason, we can't use the default arg of `dict.get`, and so instead use `or` logic.
        body = issue.get("body") or ""
        labels = [label["name"] for label in issue["labels"]]

        embed = discord.Embed(title=title)
        embed.description = body[:500] + "..." if len(body) > 500 else body
        embed.add_field(name="labels", value="\n".join(labels))
        embed.url = issue_url
        embed.set_footer(text=issue_url)

        return embed


async def setup(bot: Bot) -> None:
    """Load the HacktoberIssue finder."""
    await bot.add_cog(HacktoberIssues(bot))

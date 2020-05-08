import datetime
import logging
import random
from typing import Dict, Optional

import aiohttp
import discord
from discord.ext import commands

log = logging.getLogger(__name__)

URL = "https://api.github.com/search/issues?per_page=100&q=is:issue+label:hacktoberfest+language:python+state:open"
HEADERS = {"Accept": "application / vnd.github.v3 + json"}


class HacktoberIssues(commands.Cog):
    """Find a random hacktober python issue on GitHub."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache_normal = None
        self.cache_timer_normal = datetime.datetime(1, 1, 1)
        self.cache_beginner = None
        self.cache_timer_beginner = datetime.datetime(1, 1, 1)

    @commands.command()
    async def hacktoberissues(self, ctx: commands.Context, option: str = "") -> None:
        """
        Get a random python hacktober issue from Github.

        If the command is run with beginner (`.hacktoberissues beginner`):
        It will also narrow it down to the "first good issue" label.
        """
        with ctx.typing():
            issues = await self.get_issues(ctx, option)
            if issues is None:
                return
            issue = random.choice(issues["items"])
            embed = self.format_embed(issue)
        await ctx.send(embed=embed)

    async def get_issues(self, ctx: commands.Context, option: str) -> Optional[Dict]:
        """Get a list of the python issues with the label 'hacktoberfest' from the Github api."""
        if option == "beginner":
            if (ctx.message.created_at - self.cache_timer_beginner).seconds <= 60:
                log.debug("using cache")
                return self.cache_beginner
        elif (ctx.message.created_at - self.cache_timer_normal).seconds <= 60:
            log.debug("using cache")
            return self.cache_normal

        async with aiohttp.ClientSession() as session:
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
            async with session.get(url, headers=HEADERS) as response:
                if response.status != 200:
                    log.error(f"expected 200 status (got {response.status}) from the GitHub api.")
                    await ctx.send(f"ERROR: expected 200 status (got {response.status}) from the GitHub api.")
                    await ctx.send(await response.text())
                    return None
                data = await response.json()

                if len(data["items"]) == 0:
                    log.error(f"no issues returned from GitHub api. with url: {response.url}")
                    await ctx.send(f"ERROR: no issues returned from GitHub api. with url: {response.url}")
                    return None

                if option == "beginner":
                    self.cache_beginner = data
                    self.cache_timer_beginner = ctx.message.created_at
                else:
                    self.cache_normal = data
                    self.cache_timer_normal = ctx.message.created_at

                return data

    @staticmethod
    def format_embed(issue: Dict) -> discord.Embed:
        """Format the issue data into a embed."""
        title = issue["title"]
        issue_url = issue["url"].replace("api.", "").replace("/repos/", "/")
        body = issue["body"]
        labels = [label["name"] for label in issue["labels"]]

        embed = discord.Embed(title=title)
        embed.description = body
        embed.add_field(name="labels", value="\n".join(labels))
        embed.url = issue_url
        embed.set_footer(text=issue_url)

        return embed


def setup(bot: commands.Bot) -> None:
    """Hacktober issue finder Cog Load."""
    bot.add_cog(HacktoberIssues(bot))
    log.info("hacktober-issue-finder cog loaded")

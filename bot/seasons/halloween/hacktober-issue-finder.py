import datetime
import logging
from typing import Dict, List

import aiohttp
from discord.ext import commands

log = logging.getLogger(__name__)

URL = "https://api.github.com/search/issues"
HEADERS = {"Accept": "application / vnd.github.v3 + json"}
SEARCH = "label:hacktoberfest+language:python+state:open"


class HacktoberIssues(commands.Cog):
    """Find a random hacktober python issue on GitHub."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache = None
        self.cache_timer = datetime.datetime(1, 1, 1)

    @commands.command()
    async def hacktoberissues(self, ctx: commands.Context) -> None:
        """Get a random python hacktober issue from Github."""
        with ctx.typing():
            data = await self.get_issues(ctx)
            print("need to use data somehow to commit...", data)

    async def get_issues(self, ctx: commands.Context) -> List[Dict]:
        """Get a list of the python issues with the label 'hacktoberfest' from the Github api."""
        if (ctx.message.created_at - self.cache_timer).seconds <= 60:
            return self.cache

        async with aiohttp.ClientSession() as session:
            # text = TEXT # + "+label:hacktober"
            params = {
                "q": SEARCH
            }
            async with session.get(URL, headers=HEADERS, params=params) as response:
                if response.status != 200:
                    await ctx.send(f"ERROR: expected 200 status (got {response.status}) from the GitHub api.")
                    await ctx.send(await response.text())
                data = (await response.json())["items"]
                self.cache = data
                self.cache_timer = ctx.message.created_at
                return data


def setup(bot: commands.Bot) -> None:
    """Hacktober issue finder Cog Load."""
    bot.add_cog(HacktoberIssues(bot))
    log.info("hacktober-issue-finder cog loaded")

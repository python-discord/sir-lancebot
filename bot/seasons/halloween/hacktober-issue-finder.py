import datetime
import logging
import random
from typing import Dict, List

import aiohttp
import discord
from discord.ext import commands

log = logging.getLogger(__name__)

URL = "https://api.github.com/search/issues?q=label:hacktoberfest+language:python+state:open&per_page=100"
HEADERS = {"Accept": "application / vnd.github.v3 + json"}


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
            issues = await self.get_issues(ctx)
            issue = random.choice(issues)
            embed = self.format_embed(issue)
            await ctx.send(embed=embed)

    async def get_issues(self, ctx: commands.Context) -> List[Dict]:
        """Get a list of the python issues with the label 'hacktoberfest' from the Github api."""
        if (ctx.message.created_at - self.cache_timer).seconds <= 60:
            return self.cache

        async with aiohttp.ClientSession() as session:
            # text = TEXT # + "+label:hacktober"

            async with session.get(URL, headers=HEADERS) as response:
                if response.status != 200:
                    await ctx.send(f"ERROR: expected 200 status (got {response.status}) from the GitHub api.")
                    await ctx.send(await response.text())
                data = await response.json()
                issues = data["items"]
                self.cache = issues
                self.cache_timer = ctx.message.created_at
                return issues

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

        return embed


def setup(bot: commands.Bot) -> None:
    """Hacktober issue finder Cog Load."""
    bot.add_cog(HacktoberIssues(bot))
    log.info("hacktober-issue-finder cog loaded")

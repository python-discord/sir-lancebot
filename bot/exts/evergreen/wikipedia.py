import asyncio
import datetime
import logging
import discord
from typing import Optional

from discord.ext import commands

log = logging.getLogger(__name__)

SEARCH_API = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_term}&format=json"
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/{title}"


class WikipediaCog(commands.Cog):
    """Get info from wikipedia."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.http_session = bot.http_session

    async def search_wikipedia(self, search_term: str) -> Optional[str]:
        """Search wikipedia and return the first page found."""
        async with self.http_session.get(SEARCH_API.format(search_term=search_term)) as response:
            data = await response.json()
        page = []

        search_result = data["query"]["search"]
        if len(search_result) == 0:
            return None

        # we dont like "may refere to" pages.
        for a in search_result:
            if "may refer to" in a["snippet"]:
                pass
            else:
                page.append(a["title"])
            log.info("hit a 'may refer to' page, taking result 2 (index 1)")
        return page

    @commands.command(name="wikipedia", aliases=["wiki"])
    async def w_pedia(self, ctx: commands.Context, *, search: str) -> None:
        """Gives list of item."""
        final = []
        s = ''

        title = await self.search_wikipedia(search)

        def check(user) -> bool:
            return user.author.id == ctx.author.id

        if title is None:
            await ctx.send("Sorry, we could not find a wikipedia article using that search term")
            return

        for i in title:
            t = i.replace(" ", "_")  # wikipedia uses "_" as spaces
            final.append(t)

        async with ctx.typing():
            for index, (a, j) in enumerate(zip(title, final), start=1):
                s = s + f'`{index}` [{a}]({WIKIPEDIA_URL.format(title=j)})\n'
            embed = discord.Embed(colour=discord.Color.blue(), title=f"Wikipedia results for `{search}`", description=s)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)

        embed = discord.Embed(colour=discord.Color.green(), description="Enter number to choose")
        msg = await ctx.send(embed=embed)

        try:
            user = await ctx.bot.wait_for('message', timeout=60.0, check=check)
            await ctx.send(WIKIPEDIA_URL.format(title=final[int(user.content) - 1]))

        except asyncio.TimeoutError:
            embed = discord.Embed(colour=discord.Color.red(), description=f"Time's up {ctx.author.mention}")
            await msg.edit(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Uptime Cog load."""
    bot.add_cog(WikipediaCog(bot))

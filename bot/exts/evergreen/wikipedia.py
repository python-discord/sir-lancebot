import asyncio
import datetime
import logging
from typing import List, Optional

from discord import Color, Embed, Member
from discord.ext import commands

log = logging.getLogger(__name__)

SEARCH_API = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_term}&format=json"
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/{title}"


class WikipediaCog(commands.Cog):
    """Get info from wikipedia."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.http_session = bot.http_session

    async def search_wikipedia(self, search_term: str) -> Optional[List[str]]:
        """Search wikipedia and return the first page found."""
        async with self.http_session.get(SEARCH_API.format(search_term=search_term)) as response:
            data = await response.json()
        page = []

        search_results = data["query"]["search"]
        if len(search_results) == 0:
            return None

        # we dont like "may refere to" pages.
        for search_result in search_results:
            log.info("trying to appening titles")
            if "may refer to" in search_result["snippet"]:
                pass
            else:
                page.append(search_result["title"])
        log.info("Finished appening titles")
        return page

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="wikipedia", aliases=["wiki"])
    async def w_pedia(self, ctx: commands.Context, *, search: str) -> None:
        """Returns list of your search query from wikipedia."""
        titles_no_underscore: List[str] = []
        s_desc = ''

        titles = await self.search_wikipedia(search)

        def check(user: Member) -> bool:
            return user.author.id == ctx.author.id

        if titles is None:
            await ctx.send("Sorry, we could not find a wikipedia article using that search term")
            return

        for title in titles:
            title_for_creating_link = title.replace(" ", "_")  # wikipedia uses "_" as spaces
            titles_no_underscore.append(title_for_creating_link)
        log.info("Finished appening titles with no underscore")

        async with ctx.typing():
            for index, title in enumerate(titles, start=1):
                s_desc += f'`{index}` [{title}]({WIKIPEDIA_URL.format(title=title.replace(" ", "_"))})\n'
            embed = Embed(colour=Color.blue(), title=f"Wikipedia results for `{search}`", description=s_desc)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)
        embed = Embed(colour=Color.green(), description="Enter number to choose")
        msg = await ctx.send(embed=embed)
        chances = 0
        l_of_list = len(titles_no_underscore)  # getting length of list

        while chances <= 3:
            chances += 1
            if chances < 3:
                error_msg = f'You have `{3 - chances}/3` chances left'
            else:
                error_msg = 'Please try again by using `.wiki` command'
            try:
                user = await ctx.bot.wait_for('message', timeout=60.0, check=check)
                response_from_user = await self.bot.get_context(user)
                if response_from_user.command:
                    return
                response = int(user.content)
                if response < 0:
                    await ctx.send(f"Sorry, but you can't give negative index, {error_msg}")
                elif response == 0:
                    await ctx.send(f"Sorry, please give the range between `1` to `{len(l_of_list)}`, {error_msg}")
                else:
                    await ctx.send(WIKIPEDIA_URL.format(title=titles_no_underscore[response - 1]))
                    break

            except asyncio.TimeoutError:
                embed = Embed(colour=Color.red(), description=f"Time's up {ctx.author.mention}")
                await msg.edit(embed=embed)
                break

            except ValueError:
                await ctx.send(f"Sorry, but you cannot do that, I will only accept an integer, {error_msg}")

            except IndexError:
                await ctx.send(f"Sorry, please give the range between `1` to {l_of_list}, {error_msg}")


def setup(bot: commands.Bot) -> None:
    """Uptime Cog load."""
    bot.add_cog(WikipediaCog(bot))

import asyncio
import datetime
import logging
from typing import List, Optional

from discord import Color, Embed, Message
from discord.ext import commands

from bot.constants import Wikipedia

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
        if not search_results:
            return None

        # we dont like "may refere to" pages.
        for search_result in search_results:
            log.info("trying to append titles")
            if "may refer to" in search_result["snippet"]:
                pass
            else:
                page.append(search_result["title"])
        log.info("Finished appending titles")
        return page

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="wikipedia", aliases=["wiki"])
    async def wikipedia_search_command(self, ctx: commands.Context, *, search: str) -> None:
        """Returns list of your search query from wikipedia."""
        titles_no_underscore: List[str] = []
        s_desc = ''

        titles = await self.search_wikipedia(search)

        def check(message: Message) -> bool:
            return message.author.id == ctx.author.id

        if titles is None:
            await ctx.send("Sorry, we could not find a wikipedia article using that search term")
            return

        for title in titles:
            title_for_creating_link = title.replace(" ", "_")  # wikipedia uses "_" as spaces
            titles_no_underscore.append(title_for_creating_link)
        log.info("Finished appending titles to titles_no_underscore list")

        async with ctx.typing():
            for index, title in enumerate(titles, start=1):
                s_desc += f'`{index}` [{title}]({WIKIPEDIA_URL.format(title=title.replace(" ", "_"))})\n'
            embed = Embed(colour=Color.blue(), title=f"Wikipedia results for `{search}`", description=s_desc)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)
        embed = Embed(colour=Color.green(), description="Enter number to choose")
        msg = await ctx.send(embed=embed)
        chances = 0
        total_chances = Wikipedia.total_chance
        l_of_list = len(titles_no_underscore)  # getting length of list

        while chances <= total_chances:
            chances += 1
            if chances < total_chances:
                error_msg = f'You have `{total_chances - chances}/{total_chances}` chances left'
            else:
                error_msg = 'Please try again by using `.wiki` command'
            try:
                message: Message = await ctx.bot.wait_for('message', timeout=60.0, check=check)
                response_from_user = await self.bot.get_context(message)
                if response_from_user.command:
                    return
                response = int(message.content)
                if response < 0:
                    await ctx.send(f"Sorry, but you can't give negative index, {error_msg}")
                elif response == 0:
                    await ctx.send(f"Sorry, please give an integer between `1` to `{l_of_list}`, {error_msg}")
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
                await ctx.send(f"Sorry, please give an integer between `1` to `{l_of_list}`, {error_msg}")


def setup(bot: commands.Bot) -> None:
    """Uptime Cog load."""
    bot.add_cog(WikipediaCog(bot))

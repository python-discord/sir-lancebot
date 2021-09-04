from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from discord.ext import commands

from bot.bot import Bot

GET_KATA_LINK = 'https://codewars.com/kata/search/{lang}?q={search}&r[]={level}&beta=false'


class Challenges(commands.Cog):
    """
    Cog for a challenge command.

    Pulls a random kata from codewars.com, and can be filtered through.
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(aliases=["kata"])
    async def challenge(self, ctx: commands.Context, *, query: str) -> None:
        """Challenge command."""
        query = query.split(',' if ', ' not in query else ', ')
        kata = quote_plus(f"-{query[1]}" if len(query) > 1 else "-8")
        language = quote_plus(query[2] if len(query) > 2 else 'python')
        query = quote_plus(query[0])
        async with self.bot.http_session.get(GET_KATA_LINK.format(lang=language, search=query, level=kata)) as response:
            soup = BeautifulSoup(await response.text(), features='lxml')
            await ctx.send(soup)


def setup(bot: Bot) -> None:
    """Sets up Challenges cog."""
    bot.add_cog(Challenges(bot))

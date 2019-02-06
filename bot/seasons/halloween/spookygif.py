import logging

import aiohttp
import discord
from discord.ext import commands

from bot.constants import Tokens

log = logging.getLogger(__name__)


class SpookyGif:
    """
    A cog to fetch a random spooky gif from the web!
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="spookygif", aliases=("sgif", "scarygif"))
    async def spookygif(self, ctx):
        """
        Fetches a random gif from the GIPHY API and responds with it.
        """

        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                params = {'api_key': Tokens.giphy, 'tag': 'halloween', 'rating': 'g'}
                # Make a GET request to the Giphy API to get a random halloween gif.
                async with session.get('http://api.giphy.com/v1/gifs/random', params=params) as resp:
                    data = await resp.json()
                url = data['data']['image_url']

                embed = discord.Embed(colour=0x9b59b6)
                embed.title = "A spooooky gif!"
                embed.set_image(url=url)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(SpookyGif(bot))
    log.debug("SpookyGif cog loaded")

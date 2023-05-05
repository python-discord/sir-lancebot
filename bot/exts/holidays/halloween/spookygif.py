import logging

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, Tokens

log = logging.getLogger(__name__)

API_URL = "http://api.giphy.com/v1/gifs/random"


class SpookyGif(commands.Cog):
    """A cog to fetch a random spooky gif from the web!"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="spookygif", aliases=("sgif", "scarygif"))
    async def spookygif(self, ctx: commands.Context) -> None:
        """Fetches a random gif from the GIPHY API and responds with it."""
        async with ctx.typing():
            params = {"api_key": Tokens.giphy.get_secret_value(), "tag": "halloween", "rating": "g"}
            # Make a GET request to the Giphy API to get a random halloween gif.
            async with self.bot.http_session.get(API_URL, params=params) as resp:
                data = await resp.json()
            url = data["data"]["images"]["downsized"]["url"]

            embed = discord.Embed(title="A spooooky gif!", colour=Colours.purple)
            embed.set_image(url=url)

        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Spooky GIF Cog load."""
    await bot.add_cog(SpookyGif(bot))

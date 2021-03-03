import logging
import requests

import discord
from discord.ext import commands

from bot.constants import Tokens

log = logging.getLogger(__name__)

UnClient_id = Tokens.unsplash_key


class EarthPhotos(commands.Cog):
    """This cog contains the command for earth photos."""

    def init(self, bot: commands.Bot):
        self.bot = bot
        self.current_channel = None

    @commands.command(aliases=["earth"])
    async def earth_photos(self, ctx: commands.Context):
        """
        Returns a random photo of earth, sourced from Unsplash.
        """
        photorequest = requests.get("https://api.unsplash.com/photos/random?query=earth&client_id=" + UnClient_id)
        photojson = photorequest.json()
        photourls = photojson.get('urls')
        urltosend = photourls.get('regular')
        userjson = photojson.get('user')
        userName = userjson.get('name')
        embed = discord.Embed(title="Earth Photo", description="A photo of Earth from Unsplash.", color=0x66ff00)
        embed.set_image(url=urltosend)
        embed.set_footer(text="Image by " + userName + " on Unsplash.")
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Cog load"""
    bot.add_cog(EarthPhotos(bot))

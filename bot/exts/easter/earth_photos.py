import aiohttp
import discord
from discord.ext import commands

from bot.constants import Tokens

UnClient_id = Tokens.unsplash_key


class EarthPhotos(commands.Cog):
    """This cog contains the command for earth photos."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.current_channel = None

    @commands.command(aliases=["earth"])
    async def earth_photos(self, ctx: commands.Context) -> None:
        """Returns a random photo of earth, sourced from Unsplash."""
        async with ctx.typing():
            async with aiohttp.ClientSession as session:
                async with session.get(
                    'https://api.unsplash.com/photos/random?query=earth&client_id=' + UnClientId) as r:
                    jsondata = await r.json()
                    linksdata = jsondata.get("urls")
                    downloadlinksdata = jsondata.get("links")
                async with session.get(
                    downloadlinksdata.get("download_location") + "?client_id=" + UnClient_id) as er:
                    pass
                await ctx.send("Still a work in progress")
                    
                    
                    
            
                    


def setup(bot: commands.Bot) -> None:
    """Load the Earth Photos cog."""
    bot.add_cog(EarthPhotos(bot))

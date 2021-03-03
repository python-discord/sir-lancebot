import discord
from discord.ext import commands

from bot.constants import Colours
from bot.constants import Tokens

UnClient_id = Tokens.unsplash_key


class EarthPhotos(commands.Cog):
    """This cog contains the command for earth photos."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["earth"])
    async def earth_photos(self, ctx: commands.Context) -> None:
        """Returns a random photo of earth, sourced from Unsplash."""
        async with ctx.typing():
            async with self.bot.http_session.get(
                    'https://api.unsplash.com/photos/random',
                    params={"query": "earth", "client_id": UnClient_id}) as r:
                jsondata = await r.json()
                linksdata = jsondata.get("urls")
                embedlink = linksdata.get("regular")
                downloadlinksdata = jsondata.get("links")
                userdata = jsondata.get("user")
                username = userdata.get("name")
                userlinks = userdata.get("links")
                profile = userlinks.get("html")
            async with self.bot.http_session.get(
                downloadlinksdata.get("download_location"),
                    params={"client_id": UnClient_id}) as er:
                er.status
            embed = discord.Embed(
                title="Earth Photo",
                description="A photo of earth from Unsplash.",
                color=Colours.grass_green)
            embed.set_image(url=embedlink)
            embed.add_field(name="Author", value=f"Made by [{username}]({profile}) on Unsplash.")
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Load the Earth Photos cog."""
    bot.add_cog(EarthPhotos(bot))

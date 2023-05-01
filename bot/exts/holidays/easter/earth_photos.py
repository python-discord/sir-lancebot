import logging

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, Tokens

log = logging.getLogger(__name__)

API_URL = "https://api.unsplash.com/photos/random"


class EarthPhotos(commands.Cog):
    """This cog contains the command for earth photos."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(aliases=("earth",))
    async def earth_photos(self, ctx: commands.Context) -> None:
        """Returns a random photo of earth, sourced from Unsplash."""
        async with ctx.typing():
            async with self.bot.http_session.get(
                    API_URL,
                    params={"query": "planet_earth", "client_id": Tokens.unsplash}
            ) as r:
                jsondata = await r.json()
                linksdata = jsondata.get("urls")
                embedlink = linksdata.get("regular")
                downloadlinksdata = jsondata.get("links")
                userdata = jsondata.get("user")
                username = userdata.get("name")
                userlinks = userdata.get("links")
                profile = userlinks.get("html")
                # Referral flags
                rf = "?utm_source=Sir%20Lancebot&utm_medium=referral"
            async with self.bot.http_session.get(
                downloadlinksdata.get("download_location"),
                    params={"client_id": Tokens.unsplash}
            ) as _:
                pass

            embed = discord.Embed(
                title="Earth Photo",
                description="A photo of Earth 🌎 from Unsplash.",
                color=Colours.grass_green
            )
            embed.set_image(url=embedlink)
            embed.add_field(
                name="Author",
                value=(
                    f"Photo by [{username}]({profile}{rf}) "
                    f"on [Unsplash](https://unsplash.com{rf})."
                )
            )
            await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the Earth Photos cog."""
    if not Tokens.unsplash:
        log.warning("No Unsplash access key found. Cog not loading.")
        return
    await bot.add_cog(EarthPhotos(bot))

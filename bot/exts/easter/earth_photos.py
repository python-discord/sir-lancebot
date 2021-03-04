import logging

import discord
from discord.ext import commands

from bot.constants import Colours
from bot.constants import Tokens

log = logging.getLogger(__name__)


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
                    params={"query": "planet_earth", "client_id": Tokens.unsplash_access_key}
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
                    params={"client_id": Tokens.unsplash_access_key}
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
                value=f"Photo by [{username}]({profile}{rf}) \
                on [Unsplash](https://unsplash.com{rf})."
            )
            await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Load the Earth Photos cog."""
    if not Tokens.unsplash_access_key:
        log.warning("No Unsplash access key found. Cog not loading.")
        return
    bot.add_cog(EarthPhotos(bot))

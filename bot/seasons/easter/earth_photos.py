import json
import logging
import random
from pathlib import Path

import discord
from discord.ext import commands

log = logging.getLogger(__name__)

images = json.load(open(Path("bot/resources/easter/earth_photos.json"), 'r'))


class EarthPhotos(commands.Cog):
    """A cog that generates a spooky monster biography."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(brief="Sends an earth photo")
    async def earthphoto(self, ctx: commands.Context) -> None:
        """Sends an earth photo."""
        photo_id = random.randint(1, len(images))
        photo = images[photo_id-1]
        photo_url = photo[0]
        photographer = photo[1]
        embed = discord.Embed(title=f"Photo #{photo_id+1}")
        embed.set_image(url=photo_url)
        embed.set_footer(text=f"Photo courtesy of {photographer} from Unsplash.")
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Earth Photos Cog load."""
    bot.add_cog(EarthPhotos(bot))
    log.info("EarthPhotos cog loaded.")

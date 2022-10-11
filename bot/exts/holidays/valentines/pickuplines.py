import logging
import random
from json import loads
from pathlib import Path

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

log = logging.getLogger(__name__)

PICKUP_LINES = loads(Path("bot/resources/holidays/valentines/pickup_lines.json").read_text("utf8"))


class PickupLine(commands.Cog):
    """A cog that gives random cheesy pickup lines."""

    @commands.command()
    async def pickupline(self, ctx: commands.Context) -> None:
        """
        Gives you a random pickup line.

        Note that most of them are very cheesy.
        """
        random_line = random.choice(PICKUP_LINES["lines"])
        embed = discord.Embed(
            title=":cheese: Your pickup line :cheese:",
            description=random_line["line"],
            color=Colours.pink
        )
        embed.set_thumbnail(
            url=random_line.get("image", PICKUP_LINES["placeholder"])
        )
        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the Pickup lines Cog."""
    await bot.add_cog(PickupLine())

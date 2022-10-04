import bisect
import json
import logging
import random
from pathlib import Path

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

log = logging.getLogger(__name__)

data: dict[str, dict[str, str]] = json.loads(
    Path("bot/resources/holidays/halloween/spooky_rating.json").read_text("utf8")
)
SPOOKY_DATA = sorted((int(key), value) for key, value in data.items())


class SpookyRating(commands.Cog):
    """A cog for calculating one's spooky rating."""

    def __init__(self):
        self.local_random = random.Random()

    @commands.command()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def spookyrating(self, ctx: commands.Context, who: discord.Member = None) -> None:
        """
        Calculates the spooky rating of someone.

        Any user will always yield the same result, no matter who calls the command
        """
        if who is None:
            who = ctx.author

        # This ensures that the same result over multiple runtimes
        self.local_random.seed(who.id)
        spooky_percent = self.local_random.randint(1, 101)

        # We need the -1 due to how bisect returns the point
        # see the documentation for further detail
        # https://docs.python.org/3/library/bisect.html#bisect.bisect
        index = bisect.bisect(SPOOKY_DATA, (spooky_percent,)) - 1

        _, data = SPOOKY_DATA[index]

        embed = discord.Embed(
            title=data["title"],
            description=f"{who} scored {spooky_percent}%!",
            color=Colours.orange
        )
        embed.add_field(
            name="A whisper from Satan",
            value=data["text"]
        )
        embed.set_thumbnail(
            url=data["image"]
        )

        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the Spooky Rating Cog."""
    await bot.add_cog(SpookyRating())

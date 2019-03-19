import bisect
import json
import logging
import random
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)

with Path('bot', 'resources', 'halloween', 'spooky_rating.json').open() as file:
    SPOOKY_DATA = json.load(file)
    SPOOKY_DATA = sorted((int(key), value) for key, value in SPOOKY_DATA.items())


class SpookyRating:
    """
    A cog for calculating one's spooky rating
    """

    def __init__(self, bot):
        self.bot = bot
        self.local_random = random.Random()

    @commands.command()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def spookyrating(self, ctx, who: discord.Member = None):
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
            title=data['title'],
            description=f'{who} scored {spooky_percent}%!',
            color=Colours.orange
        )
        embed.add_field(
            name='A whisper from Satan',
            value=data['text']
        )
        embed.set_thumbnail(
            url=data['image']
        )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(SpookyRating(bot))
    log.info("SpookyRating cog loaded")

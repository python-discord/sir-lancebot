import logging
import random
from json import load
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)

with open(Path('bot', 'resources', 'valentines', 'pickup_lines.json'), 'r', encoding="utf8") as f:
    pickup_lines = load(f)


class PickupLine:
    """
    A cog that gives random cheesy pickup lines.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def pickupline(self, ctx):
        """
        Gives you a random pickup line. Note that most of them are very cheesy!
        """
        random_line = random.choice(pickup_lines['lines'])
        embed = discord.Embed(
            title=':cheese: Your pickup line :cheese:',
            description=random_line['line'],
            color=Colours.pink
        )
        embed.set_thumbnail(
            url=random_line.get('image', pickup_lines['placeholder'])
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(PickupLine(bot))
    log.info('Pickup line cog loaded')

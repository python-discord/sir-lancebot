import bisect
import hashlib
import json
import logging
import random
from pathlib import Path

import discord
from discord import Member
from discord.ext import commands
from discord.ext.commands import clean_content
from typing import Union

from bot.constants import Roles

log = logging.getLogger(__name__)

with Path('bot', 'resources', 'valentines', 'love_matches.json').open() as file:
    LOVE_DATA = json.load(file)
    LOVE_DATA = sorted((int(key), value) for key, value in LOVE_DATA.items())


class LoveCalculator:
    """
    A cog for calculating the love between two people
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=('love_calculator', 'love_calc'))
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def love(self, ctx, who: Union[Member, str], whom: Union[Member, str] = None):
        """
        Tells you how much the two love each other.
        """
        # TODO better docstring
        # figure out how to cram info about the intricacies of the command somehow
        # - member conversion
        # - asymmetry
        # - consistency (from hashing)
        # - need for quotes
        # - I'm probably forgetting something

        if whom is None:
            staff = ctx.guild.get_role(Roles.helpers).members
            whom = random.choice(staff)

        # if inputs were members, make sure to show name#discrim
        # also make sure to escape all discord markdown to prevent mischief
        cleaner = clean_content(escape_markdown=True, use_nicknames=False)
        who, whom = [await cleaner.convert(ctx, str(arg)) for arg in (who, whom)]

        # hash inputs to guarantee consistent results (hashing algorithm choice arbitrary)
        #
        # hashlib is used over the builtin hash() function
        # to guarantee same result over multiple runtimes
        # TODO: make it so `a ab` and `aa b` yield different results?
        m = hashlib.sha256(who.encode() + whom.encode())
        # mod 101 for [0, 100]
        love_percent = sum(m.digest()) % 101

        # We need the -1 due to how bisect returns the point
        # see the documentation for further detail
        # https://docs.python.org/3/library/bisect.html#bisect.bisect
        index = bisect.bisect(LOVE_DATA, (love_percent,)) - 1
        # we already have the nearest "fit" love level
        # we only need the dict, so we can ditch the first element
        _, data = LOVE_DATA[index]

        status = random.choice(data['titles'])
        embed = discord.Embed(
            title=status,
            description=f'{who} \N{HEAVY BLACK HEART} {whom} scored {love_percent}%!\n\u200b',
            color=discord.Color.dark_magenta()
        )
        embed.add_field(
            name='A letter from Dr. Love:',
            value=data['text']
        )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(LoveCalculator(bot))

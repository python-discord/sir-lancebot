import bisect
import hashlib
import json
import logging
import random
from pathlib import Path
from typing import Union

import discord
from discord import Member
from discord.ext import commands
from discord.ext.commands import BadArgument, clean_content

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

        This command accepts users or arbitrary strings as arguments.
        Users are converted from:
          - User ID
          - Mention
          - name#discrim
          - name
          - nickname

        Any two arguments will always yield the same result, though the order of arguments matters:
          Running .love joseph erlang will always yield the same result.
          Running .love erlang joseph won't yield the same result as .love joseph erlang

        If you want to use multiple words for one argument, you must include quotes.
          .love "Zes Vappa" "morning coffee"

        If only one argument is provided, the subject will become one of the helpers at random.
        """

        if whom is None:
            staff = ctx.guild.get_role(Roles.helpers).members
            whom = random.choice(staff)

        def normalize(arg):
            if isinstance(arg, Member):
                # if we are given a member, return name#discrim without any extra changes
                arg = str(arg)
            else:
                # otherwise normalise case and remove any leading/trailing whitespace
                arg = arg.strip().title()
            # this has to be done manually to be applied to usernames
            return clean_content(escape_markdown=True).convert(ctx, arg)

        who, whom = [await normalize(arg) for arg in (who, whom)]

        # make sure user didn't provide something silly such as 10 spaces
        if not (who and whom):
            raise BadArgument('Arguments be non-empty strings.')

        # hash inputs to guarantee consistent results (hashing algorithm choice arbitrary)
        #
        # hashlib is used over the builtin hash() function
        # to guarantee same result over multiple runtimes
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

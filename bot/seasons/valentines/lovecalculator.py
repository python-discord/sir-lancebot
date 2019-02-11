import json
import logging
from pathlib import Path
from random import choice

import discord
from discord.ext import commands

from bot.constants import Roles

log = logging.getLogger(__name__)


class LoveCalculator:
    """
    A cog for calculating the love between two people
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=('love_calculator', 'love_calc'))
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def love(self, ctx, name_one: discord.Member, name_two=None):
        """
        Calculates the love between two given names

        DO NOT SPAM @mentions! There are five ways to hand over a name to this command:
        1. ID of the user
        2. Name + Discriminator of the user (name#discrim) (1)
        3. Username (1)
        4. Nickname (1)
        5. @mention

        Using method 1-4 is highly encouraged, as nobody likes unwanted pings + they'll count as spam.
        Skipping the second name will lead to something awesome.

        *(1): If the name has any form of spacing, the name must be wrapped inside quotes. Example:
                .love Ves Zappa Niko Laus -> Will not work
                .love "Ves Zappa" "Niko Laus" -> Will work
        """

        if name_two is None:
            staff = ctx.guild.get_role(Roles().helpers).members
            name_two = choice(staff)
        else:
            name_two = await commands.MemberConverter().convert(ctx, name_two)
            print(name_two)

        with open(Path("bot", "resources", "valentines", "love_matches.json"), "r") as file:
            LOVE_DATA = json.load(file)
        LOVE_LEVELS = [int(x) for x in LOVE_DATA]

        love_meter = (name_one.id + name_two.id) % 100
        love_idx = str(sorted(x for x in LOVE_LEVELS if x <= love_meter)[-1])
        love_status = choice(LOVE_DATA[love_idx]["titles"])

        embed = discord.Embed(
            title=love_status,
            description=f'{name_one.display_name} \u2764 {name_two.display_name} scored {love_meter}%!\n\u200b',
            color=discord.Color.dark_magenta()
        )
        embed.add_field(
            name='A letter from Dr. Love:',
            value=LOVE_DATA[love_idx]["text"]
        )

        await ctx.message.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(LoveCalculator(bot))

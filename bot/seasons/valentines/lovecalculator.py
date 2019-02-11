# created by 3bodyZZ on 2/11/2019 @ 9 pm GMT+3

import logging
import random
from json import load
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)


class LoveCalc:
    """
    A cog that gives random percentage love values, for 2 input names,
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lovecalculator", aliases=("lovecalc",), brief="gives random values")
    async def love_calculator(self, ctx, arg1, arg2):
            percentage = random.randint(1, 100)
            # feel free to add more messages later
            with open(Path('bot', 'resources', 'valentines', 'love_calculator_messages.json'), 'r', encoding='utf8') as f:
                messages = load(f)
                if percentage <= 50:
                    polarity = 'neg'
                elif percentage >= 51:
                    polarity = "pos"

                embed = discord.Embed(
                    title="The Love percentage between" + " " + arg1 + " and " + arg2 + " is " + str(percentage) + "%",
                    description=f"{messages[polarity]}",
                    colour=Colours.pink
                )
                await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(LoveCalc(bot))
    log.debug("Love calculator cog loaded")

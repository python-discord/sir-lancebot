import itertools

import discord
from discord.ext import commands

from bot.constants import Colours

with open('bot/resources/evergreen/python_facts.txt') as file:
    FACTS = list(file)
    FACT_CYCLE = itertools.cycle(FACTS)

COLORS = [Colours.python_blue, Colours.python_yellow]
COLOR_CYCLE = itertools.cycle(COLORS)


class PythonFacts(commands.Cog):
    """Sends a random fun fact about Python."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name='pythonfact', aliases=['pyfact'])
    async def get_python_fact(self, ctx: commands.Context) -> None:
        """Sends a Random fun fact about Python."""
        embed = discord.Embed(title='Python Facts', description=next(FACT_CYCLE), colour=next(COLOR_CYCLE))
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Load PythonFacts Cog."""
    bot.add_cog(PythonFacts(bot))

import itertools

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

with open("bot/resources/utilities/python_facts.txt") as file:
    FACTS = itertools.cycle(list(file))

COLORS = itertools.cycle([Colours.python_blue, Colours.python_yellow])
PYFACTS_DISCUSSION = "https://github.com/python-discord/meta/discussions/93"


class PythonFacts(commands.Cog):
    """Sends a random fun fact about Python."""

    @commands.command(name="pythonfact", aliases=("pyfact",))
    async def get_python_fact(self, ctx: commands.Context) -> None:
        """Sends a Random fun fact about Python."""
        embed = discord.Embed(
            title="Python Facts",
            description=next(FACTS),
            colour=next(COLORS)
        )
        embed.add_field(
            name="Suggestions",
            value=f"Suggest more facts [here!]({PYFACTS_DISCUSSION})"
        )
        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the PythonFacts Cog."""
    await bot.add_cog(PythonFacts())

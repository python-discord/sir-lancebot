import itertools

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

with open('bot/resources/evergreen/python_facts.txt') as file:
    FACTS = itertools.cycle(list(file))

COLORS = itertools.cycle([Colours.python_blue, Colours.python_yellow])


class PythonFacts(commands.Cog):
    """Sends a random fun fact about Python."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.command(name='pythonfact', aliases=['pyfact'])
    async def get_python_fact(self, ctx: commands.Context) -> None:
        """Sends a Random fun fact about Python."""
        embed = discord.Embed(title='Python Facts',
                                    description=next(FACTS),
                                    colour=next(COLORS))
        embed.add_field(name='Suggestions',
                        value="Suggest more facts [here!](https://github.com/python-discord/meta/discussions/93)")
        await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Load the PythonFacts Cog."""
    bot.add_cog(PythonFacts(bot))

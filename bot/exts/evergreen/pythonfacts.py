import random

import discord
from discord.ext import commands


with open('bot/resources/evergreen/python_facts.txt') as file:
    FACTS = list(file)


class PythonFacts(commands.Cog):
    """Gives a random fun fact about Python."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name='pythonfact', aliases=['pyfact'])
    async def get_python_fact(self, ctx: commands.Context) -> None:
        """Sends a Random fun fact about Python."""
        await ctx.send(embed=discord.Embed(title='Python Facts', description=random.choice(FACTS)))


def setup(bot: commands.Bot) -> None:
    """Load PythonFacts Cog."""
    bot.add_cog(PythonFacts(bot))

import random

import discord
from discord.ext import commands
from discord.ext.commands.bot import Bot


class PythonFacts(commands.Cog):
    """Gives a random fun fact about Python."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name='pythonfact', aliases=['pyfact'])
    async def get_python_fact(self, ctx: commands.Context) -> None:
        """Gives a Random fun fact about Python."""
        with open('bot/resources/evergreen/python_facts.txt') as file:
            await ctx.send(embed=discord.Embed(title='Python Facts', description=f'**{random.choice(list(file))}**'))


def setup(bot: commands.Bot) -> None:
    """Adding the cog to the bot."""
    bot.add_cog(PythonFacts(bot))

import logging
import random

from discord.ext import commands

from bot.constants import Emojis

log = logging.getLogger(__name__)


class Fun:
    """
    A collection of general commands for fun.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, num_rolls: int = 1):
        """
            Outputs a number of random dice emotes (up to 6)
        """
        output = ""
        if num_rolls > 6:
            num_rolls = 6
        elif num_rolls < 1:
            output = ":no_entry: You must roll at least once."
        for _ in range(num_rolls):
            terning = f"terning{random.randint(1, 6)}"
            output += getattr(Emojis, terning, '')
        await ctx.send(output)


# Required in order to load the cog, use the class name in the add_cog function.
def setup(bot):
    bot.add_cog(Fun(bot))
    log.debug("Fun cog loaded")

import logging
import random

from discord.ext import commands

log = logging.getLogger(__name__)


class Fun:
    """
    A collection of general commands for fun.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, num_rolls: int):
        output = ""
        if num_rolls > 6:
            num_rolls = 6
        elif num_rolls < 0:
            output = ":no_entry: You must roll at least once."
        for _ in range(num_rolls):
            output += ":terning%d: " % random.randint(1, 6)
        await ctx.send(output)


# Required in order to load the cog, use the class name in the add_cog function.
def setup(bot):
    bot.add_cog(Fun(bot))
    log.debug("Fun cog loaded")

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
    async def roll(self, ctx, str_input: str = None):
        output = ""

        if not str_input:
            output = "To use .roll, format it as such: .roll (number)"
        else:
            try:
                num_rolls = int(str_input)
                if num_rolls > 6:
                    num_rolls = 6
                elif num_rolls < 1:
                    return
                for i in range(num_rolls):
                    output += ":terning%d: " % random.randint(1, 6)
            except ValueError:
                return
        await ctx.send(output)


# Required in order to load the cog, use the class name in the add_cog function.
def setup(bot):
    bot.add_cog(Fun(bot))
    log.debug("Fun cog loaded")

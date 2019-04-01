import json
import logging
import random
from pathlib import Path

from discord.ext import commands

log = logging.getLogger(__name__)


class Magic8ball:
    """
    A Magic 8ball command to respond to a users question.
    """

    def __init__(self, bot):
        self.bot = bot
        with open(Path("bot", "resources", "evergreen", "magic8ball.json"), "r") as file:
            self.answers = json.load(file)

    @commands.command(name="8ball")
    async def output_answer(self, ctx, *, question):
        """
        Return a magic 8 ball answer from answers list.
        """
        if len(question.split()) >= 3:
            answer = random.choice(self.answers)
            await ctx.send(answer)
        else:
            await ctx.send("Usage: .8ball <question> (minimum length of 3 eg: `will I win?`)")


# Required in order to load the cog, use the class name in the add_cog function.
def setup(bot):
    bot.add_cog(Magic8ball(bot))
    log.info("Magic 8ball cog loaded")

import logging
import random

from discord.ext import commands

log = logging.getLogger(__name__)


answers = [
    "It is certain",
    "It is decidedly so",
    "Without a doubt",
    "Yes definitely",
    "You may rely on it",
    "As I see it, yes",
    "Most likely",
    "Outlook good",
    "Yes",
    "Signs point to yes",
    "Reply hazy try again",
    "Ask again later",
    "Better not tell you now",
    "Cannot predict now",
    "Concentrate and ask again",
    "Don't count on it",
    "My reply is no",
    "My sources say no",
    "Outlook not so good",
    "Very doubtful",
]


class Magic_8ball:
    """
    A Magic 8ball command to respond to a users question.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="8ball")
    async def output_answer(self, ctx, question: list):
        """
        Return a magic 8 ball answer from answers list.
        """

        if len(question) >= 3:
            answer = random.choice(answers)
            await ctx.send(answer)


# Required in order to load the cog, use the class name in the add_cog function.
def setup(bot):
    bot.add_cog(Magic_8ball(bot))
    log.debug("Magic 8ball cog loaded")

import json
import logging
import random
from pathlib import Path

from discord.ext import commands

log = logging.getLogger(__name__)


class Magic8ball(commands.Cog):
    """A Magic 8ball command to respond to a user's question."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open(Path("bot/resources/evergreen/magic8ball.json"), "r") as file:
            self.answers = json.load(file)

    @commands.command(name="8ball")
    async def output_answer(self, ctx: commands.Context, *, question: str) -> None:
        """Return a Magic 8ball answer from answers list."""
        if len(question.split()) >= 3:
            answer = random.choice(self.answers)
            await ctx.send(answer)
        else:
            await ctx.send("Usage: .8ball <question> (minimum length of 3 eg: `will I win?`)")


def setup(bot: commands.Bot) -> None:
    """Magic 8ball Cog load."""
    bot.add_cog(Magic8ball(bot))
    log.info("Magic8ball cog loaded")

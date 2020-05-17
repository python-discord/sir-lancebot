import json
import logging
from hashlib import sha1
from pathlib import Path

from discord.ext import commands

log = logging.getLogger(__name__)


class Magic8ball(commands.Cog):
    """A Magic 8ball command to respond to a user's question."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open(Path("bot/resources/evergreen/magic8ball.json"), "r") as file:
            self.answers = json.load(file)

    def hash_input(self, inp: str, max_: int) -> int:
        """Hash the input and return a constant number between 0 and max_."""
        return int(sha1(bytes(inp, encoding='utf-8')).hexdigest(), base=16) % max_

    @commands.command(name="8ball")
    async def output_answer(self, ctx: commands.Context, *, question: str) -> None:
        """Return a Magic 8ball answer from answers list."""
        if len(question.split()) >= 3:
            answer = self.answers[self.hash_input(f"{ctx.author.id}-{question.strip()}", len(self.answers))]
            await ctx.send(answer)
        else:
            await ctx.send("Usage: .8ball <question> (minimum length of 3 eg: `will I win?`)")


def setup(bot: commands.Bot) -> None:
    """Magic 8ball Cog load."""
    bot.add_cog(Magic8ball(bot))

import json
import logging
import random
from pathlib import Path

from discord.ext import commands

from bot.bot import Bot

log = logging.getLogger(__name__)

ANSWERS = json.loads(Path("bot/resources/fun/magic8ball.json").read_text("utf8"))


class Magic8ball(commands.Cog):
    """A Magic 8ball command to respond to a user's question."""

    @commands.command(name="8ball")
    async def output_answer(self, ctx: commands.Context, *, question: str) -> None:
        """Return a Magic 8ball answer from answers list."""
        if len(question.split()) >= 3:
            answer = random.choice(ANSWERS)
            await ctx.send(answer)
        else:
            await ctx.send("Usage: .8ball <question> (minimum length of 3 eg: `will I win?`)")


async def setup(bot: Bot) -> None:
    """Load the Magic8Ball Cog."""
    await bot.add_cog(Magic8ball())

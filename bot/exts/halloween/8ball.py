import asyncio
import json
import logging
import random
from pathlib import Path

from discord.ext import commands

from bot.bot import Bot

log = logging.getLogger(__name__)

RESPONSES = json.loads(Path("bot/resources/halloween/responses.json").read_text("utf8"))


class SpookyEightBall(commands.Cog):
    """Spooky Eightball answers."""

    @commands.command(aliases=("spooky8ball",))
    async def spookyeightball(self, ctx: commands.Context, *, question: str) -> None:
        """Responds with a random response to a question."""
        choice = random.choice(RESPONSES["responses"])
        msg = await ctx.send(choice[0])
        if len(choice) > 1:
            await asyncio.sleep(random.randint(2, 5))
            await msg.edit(content=f"{choice[0]} \n{choice[1]}")


def setup(bot: Bot) -> None:
    """Load the Spooky Eight Ball Cog."""
    bot.add_cog(SpookyEightBall())

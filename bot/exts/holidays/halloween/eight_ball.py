import asyncio
import json
import random
from pathlib import Path

from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.bot import Bot

log = get_logger(__name__)

RESPONSES = json.loads(Path("bot/resources/holidays/halloween/responses.json").read_text("utf8"))


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


async def setup(bot: Bot) -> None:
    """Load the Spooky Eight Ball Cog."""
    await bot.add_cog(SpookyEightBall())

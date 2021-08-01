import json
import logging
import random
from pathlib import Path

from discord.ext import commands

from bot.bot import Bot

log = logging.getLogger(__name__)

NAMES = json.loads(Path("bot/resources/pride/drag_queen_names.json").read_text("utf8"))


class DragNames(commands.Cog):
    """Gives a random drag queen name!"""

    @commands.command(name="dragname", aliases=("dragqueenname", "queenme"))
    async def dragname(self, ctx: commands.Context) -> None:
        """Sends a message with a drag queen name."""
        await ctx.send(random.choice(NAMES))


def setup(bot: Bot) -> None:
    """Load the Drag Names Cog."""
    bot.add_cog(DragNames())

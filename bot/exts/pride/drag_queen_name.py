import json
import logging
import random
from pathlib import Path

from discord.ext import commands

from bot.bot import Bot

log = logging.getLogger(__name__)


class DragNames(commands.Cog):
    """Gives a random drag queen name!"""

    def __init__(self):
        self.names = self.load_names()

    @staticmethod
    def load_names() -> list:
        """Loads a list of drag queen names."""
        with open(Path("bot/resources/pride/drag_queen_names.json"), "r", encoding="utf8") as f:
            return json.load(f)

    @commands.command(name="dragname", aliases=["dragqueenname", "queenme"])
    async def dragname(self, ctx: commands.Context) -> None:
        """Sends a message with a drag queen name."""
        await ctx.send(random.choice(self.names))


def setup(bot: Bot) -> None:
    """Load the Drag Queen Cog."""
    bot.add_cog(DragNames(bot))

import logging
import random
from pathlib import Path

from discord.ext import commands

log = logging.getLogger(__name__)


class DragNames(commands.Cog):
    """Gives a random drag queen name!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.names = self.load_names()

    @staticmethod
    def load_names() -> list:
        """Loads a list of drag queen names."""
        with open(Path("bot/resources/pride/drag_queen_names.txt"), "r", encoding="utf-8") as f:
            return f.readlines()

    @commands.command(name="dragname", aliases=["dragqueenname", "queenme"])
    async def dragname(self, ctx: commands.Context) -> None:
        """Sends a message with a drag queen name."""
        await ctx.send(random.choice(self.names))


def setup(bot: commands.Bot) -> None:
    """Cog loader for drag queen name generator."""
    bot.add_cog(DragNames(bot))
    log.info("Drag queen name generator cog loaded!")

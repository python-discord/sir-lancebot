import logging

from discord.ext import commands

from bot.exts.evergreen.snakes._snakes_cog import Snakes

log = logging.getLogger(__name__)


def setup(bot: commands.Bot) -> None:
    """Snakes Cog load."""
    bot.add_cog(Snakes(bot))

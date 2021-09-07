import logging

from bot.bot import Bot
from bot.exts.fun.snakes._snakes_cog import Snakes

log = logging.getLogger(__name__)


def setup(bot: Bot) -> None:
    """Load the Snakes Cog."""
    bot.add_cog(Snakes(bot))

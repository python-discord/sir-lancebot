import logging

from bot.bot import Bot
from bot.exts.evergreen.snakes._snakes_cog import Snakes

log = logging.getLogger(__name__)


def setup(bot: Bot) -> None:
    """Snakes Cog load."""
    bot.add_cog(Snakes(bot))

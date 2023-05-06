import logging

from bot.bot import Bot
from bot.constants import Tokens
from bot.exts.fun.snakes._snakes_cog import Snakes

log = logging.getLogger(__name__)


async def setup(bot: Bot) -> None:
    """Load the Snakes Cog."""
    if not Tokens.giphy:
        log.warning("No Youtube token. All youtube related commands in Snakes cog won't work.")
    await bot.add_cog(Snakes(bot))

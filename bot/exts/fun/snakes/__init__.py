
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import Tokens
from bot.exts.fun.snakes._snakes_cog import Snakes

log = get_logger(__name__)


async def setup(bot: Bot) -> None:
    """Load the Snakes Cog."""
    if not Tokens.youtube:
        log.warning("No Youtube token. All YouTube related commands in Snakes cog won't work.")
    await bot.add_cog(Snakes(bot))

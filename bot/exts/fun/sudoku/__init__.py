import logging

from bot.bot import Bot
from ._sudoku import Sudoku

log = logging.getLogger(__name__)


async def setup(bot: Bot) -> None:
    """Load the Sudoku cog."""
    await bot.add_cog(Sudoku(bot))

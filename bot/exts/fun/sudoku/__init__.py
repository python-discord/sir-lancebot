import logging

from bot.bot import Bot
from bot.exts.fun.sudoku.sudoku import Sudoku

log = logging.getLogger(__name__)


async def setup(bot: Bot) -> None:
    """Load the Sudoku Cog."""
    await bot.add_cog(Sudoku(bot))

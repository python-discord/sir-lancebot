import logging

from bot.bot import Bot
from bot.exts.fun.sudoku._sudoku import Sudoku

log = logging.getLogger(__name__)


def setup(bot: Bot) -> None:
    """Load the Sudoku Cog."""
    bot.add_cog(Sudoku(bot))

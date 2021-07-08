import random
from itertools import product

from discord.ext import commands

from bot.bot import Bot

DECK = list(product(*[(0, 1, 2)]*4))


class DuckGame:
    """A class for a single game."""

    def __init__(self,
                 rows: int = 4,
                 columns: int = 3,
                 minimum_solutions: int = 1,
                 ) -> None:
        """
        Take samples from the deck to generate a board.

        Args:
            rows (int, optional): Rows in the game board. Defaults to 4.
            columns (int, optional): Columns in the game board. Defaults to 3.
            minimum_solutions (int, optional): Minimum acceptable number of solutions in the board. Defaults to 1.
        """
        self._solutions = None
        size = rows * columns
        self.board = random.sample(DECK, size)
        while len(self.solutions) < minimum_solutions:
            self.board = random.sample(DECK, size)

    @property
    def board(self) -> list[tuple[int]]:
        """Accesses board property."""
        return self._board

    @board.setter
    def board(self, val: list[tuple[int]]) -> None:
        """Erases calculated solutions if the board changes."""
        self._solution = None
        self._board = val

    @property
    def solutions(self) -> None:
        """Calculate valid solutions and cache to avoid redoing work."""
        if self._solutions is None:
            self._solutions = set()
            for idx_a, card_a in enumerate(self.board):
                for idx_b, card_b in enumerate(self.board[idx_a+1:], start=idx_a+1):
                    """
                        Two points determine a line, and there are exactly 3 points per line in {0,1,2}^4.
                        The completion of a line will only be a duplicate point if the other two points are the same,
                        which is prevented by the triangle iteration.
                    """
                    completion = tuple(feat_a if feat_a == feat_b else 3-feat_a-feat_b
                                       for feat_a, feat_b in zip(card_a, card_b)
                                       )
                    try:
                        idx_c = self.board.index(completion)
                    except ValueError:
                        continue

                    # Indices within the solution are sorted to detect duplicate solutions modulo order.
                    solution = tuple(sorted((idx_a, idx_b, idx_c)))
                    self._solutions.add(solution)

        return self._solutions


class DuckGamesDirector(commands.Cog):
    """A cog for running Duck Duck Duck Goose games."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot


def setup(bot: Bot) -> None:
    """Load the DuckGamesDirector cog."""
    bot.add_cog(DuckGamesDirector(bot))

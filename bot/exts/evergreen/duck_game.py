import asyncio
import random
from collections import defaultdict
from io import BytesIO
from itertools import product
from pathlib import Path

import discord
from PIL import Image, ImageDraw
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

DECK = list(product(*[(0, 1, 2)]*4))

GAME_DURATION = 180

p = Path("bot", "resources", "evergreen", "all_cards.png")
ALL_CARDS = Image.open(p)
CARD_WIDTH = 155
CARD_HEIGHT = 97


def assemble_board_image(board: list[tuple[int]], rows: int, columns: int) -> Image:
    """Cut and paste images representing the given cards into an image representing the board."""
    new_im = Image.new("RGBA", (CARD_WIDTH*columns, CARD_HEIGHT*rows))
    draw = ImageDraw.Draw(new_im)
    for idx, card in enumerate(board):
        card_image = get_card_image(card)
        row, col = divmod(idx, columns)
        top, left = row * CARD_HEIGHT, col * CARD_WIDTH
        new_im.paste(card_image, (left, top))
        draw.text((left+7, top+4), str(idx))    # magic numbers are buffers for the card labels
    return new_im


def get_card_image(card: tuple[int]) -> Image:
    """Slice the image containing all the cards to get just this card."""
    row, col = divmod(as_trinary(card), 9)  # all_cards.png should have 9x9 cards
    x1 = col * CARD_WIDTH
    x2 = x1 + CARD_WIDTH
    y1 = row * CARD_HEIGHT
    y2 = y1 + CARD_HEIGHT
    return ALL_CARDS.crop((x1, y1, x2, y2))


def as_trinary(card: tuple[int]) -> int:
    """Find the card's unique index by interpreting its features as trinary."""
    return int(''.join(str(x) for x in card), base=3)


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
        self.rows = rows
        self.columns = columns
        size = rows * columns

        self._solutions = None
        self.scores = defaultdict(int)

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
        self.current_games = {}

    @commands.command(name='duckduckduckgoose', aliases=['dddg', 'duckgoose'])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.channel)
    async def start_game(self, ctx: commands.Context) -> None:
        """
        Start a game.

        The bot will post an embed with the board and will listen to the following comments for valid solutions.
        Claimed answers and the final scores will be added to this embed.
        """
        # One game at a time per channel
        if ctx.channel.id in self.current_games:
            return

        game = DuckGame()
        game.running = True
        self.current_games[ctx.channel.id] = game

        game.embed_msg = await self.send_board_embed(ctx, game)
        await asyncio.sleep(GAME_DURATION)

        """Checking for the channel ID in the currently running games is not sufficient.
           The game could have been ended by a player, and a new game already started in the same channel.
        """
        if game.running:
            try:
                del self.current_games[ctx.channel.id]
                await self.end_game(game, end_message="Time's up!")
            except KeyError:
                pass

    async def send_board_embed(self, ctx: commands.Context, game: DuckGame) -> discord.Message:
        """Create and send the initial game embed. This will be edited as the game goes on."""
        image = assemble_board_image(game.board, game.rows, game.columns)
        with BytesIO() as image_stream:
            image.save(image_stream, format="png")
            image_stream.seek(0)
            file = discord.File(fp=image_stream, filename="board.png")
        embed = discord.Embed(
            title="Duck Duck Duck Goose!",
            color=Colours.bright_green,
            footer=""
        )
        embed.set_image(url="attachment://board.png")
        return await ctx.send(embed=embed, file=file)


def setup(bot: Bot) -> None:
    """Load the DuckGamesDirector cog."""
    bot.add_cog(DuckGamesDirector(bot))

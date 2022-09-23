import logging
from collections.abc import Iterator
from dataclasses import dataclass
from random import randint, random
from typing import Union

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Client
from bot.utils.converters import CoordinateConverter
from bot.utils.exceptions import UserNotPlayingError

MESSAGE_MAPPING = {
    0: ":stop_button:",
    1: ":one:",
    2: ":two:",
    3: ":three:",
    4: ":four:",
    5: ":five:",
    6: ":six:",
    7: ":seven:",
    8: ":eight:",
    9: ":nine:",
    10: ":keycap_ten:",
    "bomb": ":bomb:",
    "hidden": ":grey_question:",
    "flag": ":flag_black:",
    "x": ":x:"
}

log = logging.getLogger(__name__)


GameBoard = list[list[Union[str, int]]]


@dataclass
class Game:
    """The data for a game."""

    board: GameBoard
    revealed: GameBoard
    dm_msg: discord.Message
    chat_msg: discord.Message
    activated_on_server: bool


class Minesweeper(commands.Cog):
    """Play a game of Minesweeper."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.games: dict[int, Game] = {}

    @commands.group(name="minesweeper", aliases=("ms",), invoke_without_command=True)
    async def minesweeper_group(self, ctx: commands.Context) -> None:
        """Commands for Playing Minesweeper."""
        await self.bot.invoke_help_command(ctx)

    @staticmethod
    def get_neighbours(x: int, y: int) -> Iterator[tuple[int, int]]:
        """Get all the neighbouring x and y including it self."""
        for x_ in [x - 1, x, x + 1]:
            for y_ in [y - 1, y, y + 1]:
                if x_ != -1 and x_ != 10 and y_ != -1 and y_ != 10:
                    yield x_, y_

    def generate_board(self, bomb_chance: float) -> GameBoard:
        """Generate a 2d array for the board."""
        board: GameBoard = [
            [
                "bomb" if random() <= bomb_chance else "number"
                for _ in range(10)
            ] for _ in range(10)
        ]

        # make sure there is always a free cell
        board[randint(0, 9)][randint(0, 9)] = "number"

        for y, row in enumerate(board):
            for x, cell in enumerate(row):
                if cell == "number":
                    # calculate bombs near it
                    bombs = 0
                    for x_, y_ in self.get_neighbours(x, y):
                        if board[y_][x_] == "bomb":
                            bombs += 1
                    board[y][x] = bombs
        return board

    @staticmethod
    def format_for_discord(board: GameBoard) -> str:
        """Format the board as a string for Discord."""
        discord_msg = (
            ":stop_button:    :regional_indicator_a: :regional_indicator_b: :regional_indicator_c: "
            ":regional_indicator_d: :regional_indicator_e: :regional_indicator_f: :regional_indicator_g: "
            ":regional_indicator_h: :regional_indicator_i: :regional_indicator_j:\n\n"
        )
        rows = []
        for row_number, row in enumerate(board):
            new_row = f"{MESSAGE_MAPPING[row_number + 1]}    "
            new_row += " ".join(MESSAGE_MAPPING[cell] for cell in row)
            rows.append(new_row)

        discord_msg += "\n".join(rows)
        return discord_msg

    @minesweeper_group.command(name="start")
    async def start_command(self, ctx: commands.Context, bomb_chance: float = .2) -> None:
        """Start a game of Minesweeper."""
        if ctx.author.id in self.games:  # Player is already playing
            await ctx.send(f"{ctx.author.mention} you already have a game running!", delete_after=2)
            await ctx.message.delete(delay=2)
            return

        try:
            await ctx.author.send(
                f"Play by typing: `{Client.prefix}ms reveal xy [xy]` or `{Client.prefix}ms flag xy [xy]` \n"
                f"Close the game with `{Client.prefix}ms end`\n"
            )
        except discord.errors.Forbidden:
            log.debug(f"{ctx.author.name} ({ctx.author.id}) has disabled DMs from server members.")
            await ctx.send(f":x: {ctx.author.mention}, please enable DMs to play minesweeper.")
            return

        # Add game to list
        board: GameBoard = self.generate_board(bomb_chance)
        revealed_board: GameBoard = [["hidden"] * 10 for _ in range(10)]
        dm_msg = await ctx.author.send(f"Here's your board!\n{self.format_for_discord(revealed_board)}")

        if ctx.guild:
            await ctx.send(f"{ctx.author.mention} is playing Minesweeper.")
            chat_msg = await ctx.send(f"Here's their board!\n{self.format_for_discord(revealed_board)}")
        else:
            chat_msg = None

        self.games[ctx.author.id] = Game(
            board=board,
            revealed=revealed_board,
            dm_msg=dm_msg,
            chat_msg=chat_msg,
            activated_on_server=ctx.guild is not None
        )

    async def update_boards(self, ctx: commands.Context) -> None:
        """Update both playing boards."""
        game = self.games[ctx.author.id]
        await game.dm_msg.delete()
        game.dm_msg = await ctx.author.send(f"Here's your board!\n{self.format_for_discord(game.revealed)}")
        if game.activated_on_server:
            await game.chat_msg.edit(content=f"Here's their board!\n{self.format_for_discord(game.revealed)}")

    @commands.dm_only()
    @minesweeper_group.command(name="flag")
    async def flag_command(self, ctx: commands.Context, *coordinates: CoordinateConverter) -> None:
        """Place multiple flags on the board."""
        if ctx.author.id not in self.games:
            raise UserNotPlayingError
        board: GameBoard = self.games[ctx.author.id].revealed
        for x, y in coordinates:
            if board[y][x] == "hidden":
                board[y][x] = "flag"

        await self.update_boards(ctx)

    @staticmethod
    def reveal_bombs(revealed: GameBoard, board: GameBoard) -> None:
        """Reveals all the bombs."""
        for y, row in enumerate(board):
            for x, cell in enumerate(row):
                if cell == "bomb":
                    revealed[y][x] = cell

    async def lost(self, ctx: commands.Context) -> None:
        """The player lost the game."""
        game = self.games[ctx.author.id]
        self.reveal_bombs(game.revealed, game.board)
        await ctx.author.send(":fire: You lost! :fire:")
        if game.activated_on_server:
            await game.chat_msg.channel.send(f":fire: {ctx.author.mention} just lost Minesweeper! :fire:")

    async def won(self, ctx: commands.Context) -> None:
        """The player won the game."""
        game = self.games[ctx.author.id]
        await ctx.author.send(":tada: You won! :tada:")
        if game.activated_on_server:
            await game.chat_msg.channel.send(f":tada: {ctx.author.mention} just won Minesweeper! :tada:")

    def reveal_zeros(self, revealed: GameBoard, board: GameBoard, x: int, y: int) -> None:
        """Recursively reveal adjacent cells when a 0 cell is encountered."""
        for x_, y_ in self.get_neighbours(x, y):
            if revealed[y_][x_] != "hidden":
                continue
            revealed[y_][x_] = board[y_][x_]
            if board[y_][x_] == 0:
                self.reveal_zeros(revealed, board, x_, y_)

    async def check_if_won(self, ctx: commands.Context, revealed: GameBoard, board: GameBoard) -> bool:
        """Checks if a player has won."""
        if any(
            revealed[y][x] in ["hidden", "flag"] and board[y][x] != "bomb"
            for x in range(10)
            for y in range(10)
        ):
            return False
        else:
            await self.won(ctx)
            return True

    async def reveal_one(
        self,
        ctx: commands.Context,
        revealed: GameBoard,
        board: GameBoard,
        x: int,
        y: int
    ) -> bool:
        """
        Reveal one square.

        return is True if the game ended, breaking the loop in `reveal_command` and deleting the game.
        """
        revealed[y][x] = board[y][x]
        if board[y][x] == "bomb":
            await self.lost(ctx)
            revealed[y][x] = "x"  # mark bomb that made you lose with a x
            return True
        elif board[y][x] == 0:
            self.reveal_zeros(revealed, board, x, y)
        return await self.check_if_won(ctx, revealed, board)

    @commands.dm_only()
    @minesweeper_group.command(name="reveal")
    async def reveal_command(self, ctx: commands.Context, *coordinates: CoordinateConverter) -> None:
        """Reveal multiple cells."""
        if ctx.author.id not in self.games:
            raise UserNotPlayingError
        game = self.games[ctx.author.id]
        revealed: GameBoard = game.revealed
        board: GameBoard = game.board

        for x, y in coordinates:
            # reveal_one returns True if the revealed cell is a bomb or the player won, ending the game
            if await self.reveal_one(ctx, revealed, board, x, y):
                await self.update_boards(ctx)
                del self.games[ctx.author.id]
                break
        else:
            await self.update_boards(ctx)

    @minesweeper_group.command(name="end")
    async def end_command(self, ctx: commands.Context) -> None:
        """End your current game."""
        if ctx.author.id not in self.games:
            raise UserNotPlayingError
        game = self.games[ctx.author.id]
        game.revealed = game.board
        await self.update_boards(ctx)
        new_msg = f":no_entry: Game canceled. :no_entry:\n{game.dm_msg.content}"
        await game.dm_msg.edit(content=new_msg)
        if game.activated_on_server:
            await game.chat_msg.edit(content=new_msg)
        del self.games[ctx.author.id]


async def setup(bot: Bot) -> None:
    """Load the Minesweeper cog."""
    await bot.add_cog(Minesweeper(bot))

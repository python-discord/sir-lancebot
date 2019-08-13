import logging
import typing
from dataclasses import dataclass
from random import random

import discord
from discord.ext import commands

from bot.constants import Client

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
    "flag": ":triangular_flag_on_post:"
}

log = logging.getLogger(__name__)


class CoordinateConverter(commands.Converter):
    """Converter for Coordinates."""

    async def convert(self, ctx, coordinate: str) -> typing.Tuple[int, int]:
        """Take in a coordinate string and turn it into x, y"""
        if not 2 <= len(coordinate) <= 3:
            raise commands.ArgumentParsingError()

        value1 = coordinate[0]
        value2 = coordinate[1:]

        if not value2.isdigit():
            raise commands.ArgumentParsingError()

        x = ord(value1) - 97
        y = int(value2) - 1

        if (not 0 <= x <= 9) or (not 0 <= y <= 9):
            raise commands.ArgumentParsingError()
        return x, y


GameBoard = typing.List[typing.List[typing.Union[str, int]]]


@dataclass
class Game:
    """The data for a game."""

    board: GameBoard
    revealed: GameBoard
    dm_msg: discord.message
    chat_msg: discord.message


GamesDict = typing.Dict[int, Game]


class Minesweeper(commands.Cog):
    """Play a game of Minesweeper."""

    def __init__(self, bot: commands.Bot) -> None:
        self.games: GamesDict = {}  # Store the currently running games

    @staticmethod
    def get_neighbours(x: int, y: int) -> typing.Generator:
        """Get all the neighbouring x and y including it self."""
        for x_ in [x - 1, x, x + 1]:
            for y_ in [y - 1, y, y + 1]:
                if x_ != -1 and x_ != 10 and y_ != -1 and y_ != 10:
                    yield x_, y_

    def generate_board(self, bomb_chance: float) -> GameBoard:
        """Generate a 2d array for the board."""
        board: GameBoard = [["bomb" if random() <= bomb_chance else "number" for _ in range(10)] for _ in range(10)]
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
            ":stop_button:    :regional_indicator_a::regional_indicator_b::regional_indicator_c:"
            ":regional_indicator_d::regional_indicator_e::regional_indicator_f::regional_indicator_g:"
            ":regional_indicator_h::regional_indicator_i::regional_indicator_j:\n\n"
        )
        rows: typing.List[str] = []
        for row_number, row in enumerate(board):
            new_row = MESSAGE_MAPPING[row_number + 1] + "    "
            for cell in row:
                new_row += MESSAGE_MAPPING[cell]
            rows.append(new_row)

        discord_msg += "\n".join(rows)
        return discord_msg

    @commands.command(name="minesweeper")
    async def minesweeper_command(self, ctx: commands.Context, bomb_chance: float = .2) -> None:
        """Start a game of Minesweeper."""
        if ctx.author.id in self.games:  # Player is already playing
            msg = await ctx.send(f"{ctx.author.mention} you already have a game running!")
            await msg.delete(delay=2)
            await ctx.message.delete(delay=2)
            return

        # Add game to list
        board: GameBoard = self.generate_board(bomb_chance)
        revealed_board: GameBoard = [["hidden"] * 10 for _ in range(10)]

        await ctx.send(f"{ctx.author.mention} is playing Minesweeper")
        chat_msg = await ctx.send(self.format_for_discord(revealed_board))

        await ctx.author.send(
            f"Play by typing: `{Client.prefix}reveal xy [xy]` or `{Client.prefix}flag xy [xy]` \n"
            f"Close the game with `{Client.prefix}end`\n"
            "Coordinates must be in format `<letter><number>`"
        )
        dm_msg = await ctx.author.send(self.format_for_discord(revealed_board))

        self.games[ctx.author.id] = Game(
            board=board,
            revealed=revealed_board,
            dm_msg=dm_msg,
            chat_msg=chat_msg
        )

    async def update_boards(self, ctx: commands.Context) -> None:
        """Update both playing boards."""
        game = self.games[ctx.author.id]
        await game.dm_msg.delete()
        game.dm_msg = await ctx.author.send(self.format_for_discord(game.revealed))
        await game.chat_msg.edit(content=self.format_for_discord(game.revealed))

    @commands.dm_only()
    @commands.command(name="flag")
    async def flag_command(self, ctx: commands.Context, *coordinates: CoordinateConverter) -> None:
        """Place multiple flags on the board"""
        board: GameBoard = self.games[ctx.author.id].revealed
        for x, y in coordinates:
            if board[y][x] == "hidden":
                board[y][x] = "flag"

        await self.update_boards(ctx)

    async def lost(self, ctx: commands.Context) -> None:
        """The player lost the game"""
        game = self.games[ctx.author.id]
        game.revealed = game.board
        await ctx.author.send(":fire: You lost! :fire:")
        await game.chat_msg.channel.send(f":fire: {ctx.author.mention} just lost Minesweeper! :fire:")

    async def won(self, ctx: commands.Context) -> None:
        """The player won the game"""
        game = self.games[ctx.author.id]
        game.revealed = game.board
        await ctx.author.send(":tada: You won! :tada:")
        await game.chat_msg.channel.send(f":tada: {ctx.author.mention} just won Minesweeper! :tada:")

    def reveal_zeros(self, revealed: GameBoard, board: GameBoard, x: int, y: int) -> None:
        """Recursively reveal adjacent cells when a 0 cell is encountered."""
        for x_, y_ in self.get_neighbours(x, y):
            if revealed[y_][x_] != "hidden":
                continue
            revealed[y_][x_] = board[y_][x_]
            if board[y_][x_] == 0:
                self.reveal_zeros(revealed, board, x_, y_)

    async def check_if_won(self, ctx, revealed: GameBoard, board: GameBoard) -> bool:
        """Checks if a player has won"""
        for x in range(10):
            for y in range(10):
                if revealed[y][x] == "hidden":
                    return False
        else:
            await self.won(ctx)
            return True

    async def reveal_one(self, ctx: commands.Context, revealed: GameBoard, board: GameBoard, x: int, y: int) -> bool:
        """
        Reveal one square.

        return is True if the game ended, breaking the loop in `reveal_command` and deleting the game
        """
        revealed[y][x] = board[y][x]
        if board[y][x] == "bomb":
            await self.lost(ctx)
            return True  # game ended
        elif board[y][x] == 0:
            self.reveal_zeros(revealed, board, x, y)
        return await self.check_if_won(ctx, revealed, board)

    @commands.dm_only()
    @commands.command(name="reveal")
    async def reveal_command(self, ctx: commands.Context, *coordinates: CoordinateConverter) -> None:
        """Reveal multiple cells"""
        game = self.games[ctx.author.id]
        revealed: GameBoard = game.revealed
        board: GameBoard = game.board

        for x, y in coordinates:
            if await self.reveal_one(ctx, revealed, board, x, y):  # game ended
                await self.update_boards(ctx)
                del self.games[ctx.author.id]
                break
        else:
            await self.update_boards(ctx)

    @commands.command(name="end")
    async def end_command(self, ctx: commands.Context):
        """End the current game"""
        game = self.games[ctx.author.id]
        game.revealed = game.board
        await self.update_boards(ctx)
        new_msg = f":no_entry: Game canceled :no_entry:\n{self.format_for_discord(game.revealed)}"
        await game.dm_msg.edit(content=new_msg)
        await game.chat_msg.edit(content=new_msg)
        del self.games[ctx.author.id]


def setup(bot: commands.Bot) -> None:
    """Load the Minesweeper cog."""
    bot.add_cog(Minesweeper(bot))
    log.info("Minesweeper cog loaded")

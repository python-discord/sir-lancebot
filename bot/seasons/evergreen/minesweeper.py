import typing
from random import random

import discord
from discord.ext import commands


class Minesweeper(commands.Cog):
    """Play a game of minesweeper."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.games: typing.Dict[discord.member, typing.Dict] = {}  # Store the currently running games

    @staticmethod
    def is_bomb(cell: typing.Union[str, int]) -> int:
        """Returns 1 if `cell` is a bomb if not 0"""
        return 1 if cell == "bomb" else 0

    def generate_board(self) -> typing.List[typing.List[typing.Union[str, int]]]:
        """Generate a 2d array for the board."""
        board: typing.List[typing.List[typing.Union[str, int]]] = [
            ["bomb" if random() <= .2 else "number" for _ in range(10)] for _ in range(9)]
        for y, row in enumerate(board):
            for x, cell in enumerate(row):
                if cell == "number":
                    # calculate bombs near it
                    to_check = []
                    for xt in [x - 1, x, x + 1]:
                        for yt in [y - 1, y, y + 1]:
                            if xt != -1 and xt != 10 and yt != -1 and yt != 9:
                                to_check.append(board[yt][xt])

                    bombs = sum(map(self.is_bomb, to_check))
                    board[y][x] = bombs
        return board

    @commands.command(name="minesweeper")
    async def minesweeper_command(self, ctx: commands.Context) -> None:
        """Start a game of minesweeper."""
        if ctx.author in self.games.keys():  # Player is already playing
            msg = await ctx.send(f"{ctx.author.mention} you already have a game running")
            await msg.delete(delay=2)
            await ctx.message.delete(delay=2)
            return

        # Add game to list
        await ctx.send(str(self.generate_board()))
        self.games[ctx.author] = {

        }


def setup(bot: commands.Bot) -> None:
    """Cog load."""
    bot.add_cog(Minesweeper(bot))

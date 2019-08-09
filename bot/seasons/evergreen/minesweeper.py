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
            ["bomb" if random() <= .2 else "number" for _ in range(10)] for _ in range(10)]
        for y, row in enumerate(board):
            for x, cell in enumerate(row):
                if cell == "number":
                    # calculate bombs near it
                    to_check = []
                    for xt in [x - 1, x, x + 1]:
                        for yt in [y - 1, y, y + 1]:
                            if xt != -1 and xt != 10 and yt != -1 and yt != 10:
                                to_check.append(board[yt][xt])

                    bombs = sum(map(self.is_bomb, to_check))
                    board[y][x] = bombs
        return board

    @staticmethod
    def format_for_discord(board: typing.List[typing.List[typing.Union[str, int]]]) -> str:
        """Format the board to a string for discord."""
        mapping = {
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

        discord_msg = ":stop_button:    :one::two::three::four::five::six::seven::eight::nine::keycap_ten:\n\n"
        rows: typing.List[str] = []
        for row_number, row in enumerate(board):
            new_row = mapping[row_number + 1] + "    "
            for cell in row:
                new_row += mapping[cell]
            rows.append(new_row)

        discord_msg += "\n".join(rows)
        return discord_msg

    @commands.command(name="minesweeper")
    async def minesweeper_command(self, ctx: commands.Context) -> None:
        """Start a game of minesweeper."""
        if ctx.author in self.games.keys():  # Player is already playing
            msg = await ctx.send(f"{ctx.author.mention} you already have a game running")
            await msg.delete(delay=2)
            await ctx.message.delete(delay=2)
            return

        # Add game to list
        board = self.generate_board()
        reveled_board = [["hidden" for _ in range(10)]for _ in range(10)]

        await ctx.send(f"{ctx.author.mention} is playing minesweeper")
        chat_msg = await ctx.send(self.format_for_discord(reveled_board))

        await ctx.author.send("play by typing: `.reveal x y` and `.flag x y`")
        dm_msg = await ctx.author.send(self.format_for_discord(reveled_board))

        self.games[ctx.author] = {
            "board": board,
            "reveled": reveled_board,
            "dm_msg": dm_msg,
            "chat_msg": chat_msg
        }


def setup(bot: commands.Bot) -> None:
    """Cog load."""
    bot.add_cog(Minesweeper(bot))

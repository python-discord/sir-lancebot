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

    def generate_board(self, bomb_chance: float) -> typing.List[typing.List[typing.Union[str, int]]]:
        """Generate a 2d array for the board."""
        board: typing.List[typing.List[typing.Union[str, int]]] = [
            ["bomb" if random() <= bomb_chance else "number" for _ in range(10)] for _ in range(10)]
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

        discord_msg = ":stop_button:    :regional_indicator_a::regional_indicator_b::regional_indicator_c:" \
                      ":regional_indicator_d::regional_indicator_e::regional_indicator_f::regional_indicator_g:" \
                      ":regional_indicator_h::regional_indicator_i::regional_indicator_j:\n\n"
        rows: typing.List[str] = []
        for row_number, row in enumerate(board):
            new_row = mapping[row_number + 1] + "    "
            for cell in row:
                new_row += mapping[cell]
            rows.append(new_row)

        discord_msg += "\n".join(rows)
        return discord_msg

    @commands.command(name="minesweeper")
    async def minesweeper_command(self, ctx: commands.Context, bomb_chance: float = .2) -> None:
        """Start a game of minesweeper."""
        if ctx.author in self.games.keys():  # Player is already playing
            msg = await ctx.send(f"{ctx.author.mention} you already have a game running")
            await msg.delete(delay=2)
            await ctx.message.delete(delay=2)
            return

        # Add game to list
        board = self.generate_board(bomb_chance)
        reveled_board = [["hidden" for _ in range(10)] for _ in range(10)]

        await ctx.send(f"{ctx.author.mention} is playing minesweeper")
        chat_msg = await ctx.send(self.format_for_discord(reveled_board))

        await ctx.author.send("play by typing: `.reveal x y` or `.flag x y` \nclose the game with `.end`")
        dm_msg = await ctx.author.send(self.format_for_discord(reveled_board))
        await ctx.author.send(self.format_for_discord(board))

        self.games[ctx.author] = {
            "board": board,
            "reveled": reveled_board,
            "dm_msg": dm_msg,
            "chat_msg": chat_msg
        }

    @staticmethod
    def get_cords(value1: str, value2: str) -> typing.Tuple[int, int]:
        """Take in 2 values for the cords and turn them into numbers"""
        if value1.isnumeric():
            return int(value1) - 1, ord(value2.lower()) - 97
        else:
            return ord(value1.lower()) - 97, int(value2) - 1

    async def reload_board(self, ctx: commands.Context) -> None:
        """Update both playing boards."""
        game = self.games[ctx.author]
        await game["dm_msg"].delete()
        game["dm_msg"] = await ctx.author.send(self.format_for_discord(game["reveled"]))
        await game["chat_msg"].edit(content=self.format_for_discord(game["reveled"]))

    @commands.dm_only()
    @commands.command(name="flag")
    async def flag_command(self, ctx: commands.Context, value1, value2) -> None:
        """Place a flag on the board"""
        x, y = self.get_cords(value1, value2)  # ints
        board = self.games[ctx.author]["reveled"]
        if board[y][x] == "hidden":
            board[y][x] = "flag"

        await self.reload_board(ctx)

    async def lost(self, ctx: commands.Context) -> None:
        """The player lost the game"""
        game = self.games[ctx.author]
        game["reveled"] = game["board"]
        await self.reload_board(ctx)
        await ctx.author.send(":fire: You lost :fire: ")
        await game["chat_msg"].channel.send(f":fire: {ctx.author.mention} just lost minesweeper :fire:")
        del self.games[ctx.author]

    async def won(self, ctx: commands.Context):
        """The player won the game"""
        game = self.games[ctx.author]
        game["reveled"] = game["board"]
        await self.reload_board(ctx)
        await ctx.author.send(":tada:  You won! :tada: ")
        await game["chat_msg"].channel.send(f":tada: {ctx.author.mention} just won minesweeper :tada:")
        del self.games[ctx.author]

    def reveal(self, reveled: typing.List, board: typing.List, x: int, y: int) -> None:
        """Used when a 0 is encountered to do a flood fill"""
        for x_ in [x - 1, x, x + 1]:
            for y_ in [y - 1, y, y + 1]:
                if x_ == -1 or x_ == 10 or y_ == -1 or y_ == 10 or reveled[y_][x_] != "hidden":
                    continue
                reveled[y_][x_] = board[y_][x_]
                if board[y_][x_] == 0:
                    self.reveal(reveled, board, x_, y_)

    @commands.dm_only()
    @commands.command(name="reveal")
    async def reveal_command(self, ctx: commands.Context, value1, value2):
        """Reveal a cell"""
        x, y = self.get_cords(value1, value2)
        game = self.games[ctx.author]
        reveled = game["reveled"]
        board = game["board"]
        reveled[y][x] = board[y][x]
        if board[y][x] == "bomb":
            await self.lost(ctx)
        elif board[y][x] == 0:
            self.reveal(reveled, board, x, y)

        # check if won
        break_ = False
        for x_ in range(10):
            for y_ in range(10):
                if reveled[y_][x_] == "hidden" and board[y_][x_] != "bomb":
                    break_ = True
                    break
            if break_:
                break
        else:
            await self.won(ctx)

        await self.reload_board(ctx)

    @commands.dm_only()
    @commands.command(name="end")
    async def end_command(self, ctx: commands.Context):
        """End the current game"""
        game = self.games[ctx.author]
        game["reveled"] = game["board"]
        await self.reload_board(ctx)
        await ctx.author.send(":no_entry: you canceled the game :no_entry:")
        await game["chat_msg"].channel.send(f"{ctx.author.mention} just canceled minesweeper")
        del self.games[ctx.author]


def setup(bot: commands.Bot) -> None:
    """Cog load."""
    bot.add_cog(Minesweeper(bot))

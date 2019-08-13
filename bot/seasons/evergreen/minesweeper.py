import typing
from random import random

from discord.ext import commands

GameBoard = typing.List[typing.List[typing.Union[str, int]]]
DictOfGames = typing.Dict[int, typing.Dict]


class CordConverter(commands.Converter):
    """Converter for cords."""

    async def convert(self, ctx, cord: str) -> typing.Tuple[int, int]:
        """Take in a cord string and turn it into x, y"""
        if not 2 <= len(cord) <= 3:
            raise commands.ArgumentParsingError()
        value1 = cord[0]
        value2 = cord[1:]
        if not value2.isdigit():
            raise commands.ArgumentParsingError()
        x = ord(value1) - 97
        y = int(value2) - 1
        if (not 0 <= x <= 9) or (not 0 <= y <= 9):
            raise commands.ArgumentParsingError()
        return x, y


class Minesweeper(commands.Cog):
    """Play a game of minesweeper."""

    def __init__(self, bot: commands.Bot) -> None:
        self.games: DictOfGames = {}  # Store the currently running games

    @staticmethod
    def is_bomb(cell: typing.Union[str, int]) -> int:
        """Returns 1 if `cell` is a bomb if not 0"""
        return cell == "bomb"

    def generate_board(self, bomb_chance: float) -> GameBoard:
        """Generate a 2d array for the board."""
        board: GameBoard = [["bomb" if random() <= bomb_chance else "number" for _ in range(10)] for _ in range(10)]
        for y, row in enumerate(board):
            for x, cell in enumerate(row):
                if cell == "number":
                    # calculate bombs near it
                    bombs = 0
                    for x_ in [x - 1, x, x + 1]:
                        for y_ in [y - 1, y, y + 1]:
                            if x_ != -1 and x_ != 10 and y_ != -1 and y_ != 10 and board[y_][x_] == "bomb":
                                bombs += 1

                    board[y][x] = bombs
        return board

    @staticmethod
    def format_for_discord(board: GameBoard) -> str:
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

        discord_msg = (
            ":stop_button:    :regional_indicator_a::regional_indicator_b::regional_indicator_c:"
            ":regional_indicator_d::regional_indicator_e::regional_indicator_f::regional_indicator_g:"
            ":regional_indicator_h::regional_indicator_i::regional_indicator_j:\n\n"
        )
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
        if ctx.author.id in self.games.keys():  # Player is already playing
            msg = await ctx.send(f"{ctx.author.mention} you already have a game running")
            await msg.delete(delay=2)
            await ctx.message.delete(delay=2)
            return

        # Add game to list
        board: GameBoard = self.generate_board(bomb_chance)
        revealed_board: GameBoard = [["hidden" for _ in range(10)] for _ in range(10)]

        await ctx.send(f"{ctx.author.mention} is playing minesweeper")
        chat_msg = await ctx.send(self.format_for_discord(revealed_board))

        await ctx.author.send("play by typing: `.reveal xy [xy]` or `.flag xy [xy]` \n"
                              "close the game with `.end`\n"
                              "cords must be in format `<letter><number>`")
        dm_msg = await ctx.author.send(self.format_for_discord(revealed_board))

        self.games[ctx.author.id] = {
            "board": board,
            "revealed": revealed_board,
            "dm_msg": dm_msg,
            "chat_msg": chat_msg
        }

    async def reload_board(self, ctx: commands.Context) -> None:
        """Update both playing boards."""
        game = self.games[ctx.author.id]
        await game["dm_msg"].delete()
        game["dm_msg"] = await ctx.author.send(self.format_for_discord(game["revealed"]))
        await game["chat_msg"].edit(content=self.format_for_discord(game["revealed"]))

    @commands.dm_only()
    @commands.command(name="flag")
    async def flag_command(self, ctx: commands.Context, *cords: CordConverter) -> None:
        """Place multiple flags on the board"""
        board: GameBoard = self.games[ctx.author.id]["revealed"]
        for x, y in cords:
            if board[y][x] == "hidden":
                board[y][x] = "flag"

        await self.reload_board(ctx)

    async def lost(self, ctx: commands.Context) -> None:
        """The player lost the game"""
        game = self.games[ctx.author.id]
        game["revealed"] = game["board"]
        await self.reload_board(ctx)
        await ctx.author.send(":fire: You lost :fire: ")
        await game["chat_msg"].channel.send(f":fire: {ctx.author.mention} just lost Minesweeper! :fire:")
        del self.games[ctx.author.id]

    async def won(self, ctx: commands.Context) -> None:
        """The player won the game"""
        game = self.games[ctx.author.id]
        game["revealed"] = game["board"]
        await self.reload_board(ctx)
        await ctx.author.send(":tada: You won! :tada: ")
        await game["chat_msg"].channel.send(f":tada: {ctx.author.mention} just won Minesweeper! :tada:")
        del self.games[ctx.author.id]

    def reveal_zeros(self, revealed: GameBoard, board: GameBoard, x: int, y: int) -> None:
        """Used when a 0 is encountered to do a flood fill"""
        for x_ in [x - 1, x, x + 1]:
            for y_ in [y - 1, y, y + 1]:
                if x_ == -1 or x_ == 10 or y_ == -1 or y_ == 10 or revealed[y_][x_] != "hidden":
                    continue
                revealed[y_][x_] = board[y_][x_]
                if board[y_][x_] == 0:
                    self.reveal_zeros(revealed, board, x_, y_)

    async def check_if_won(self, ctx, revealed: GameBoard, board: GameBoard) -> bool:
        """Checks if a player has won"""
        for x_ in range(10):
            for y_ in range(10):
                if revealed[y_][x_] == "hidden" and board[y_][x_] != "bomb":
                    return True
        else:
            await self.won(ctx)
            return False

    async def reveal_one(self, ctx: commands.Context, revealed: GameBoard, board: GameBoard, x: int, y: int) -> bool:
        """Reveal one square."""
        revealed[y][x] = board[y][x]
        if board[y][x] == "bomb":
            await self.lost(ctx)
            return False
        elif board[y][x] == 0:
            self.reveal_zeros(revealed, board, x, y)
        return await self.check_if_won(ctx, revealed, board)

    @commands.dm_only()
    @commands.command(name="reveal")
    async def reveal_command(self, ctx: commands.Context, *cords: CordConverter) -> None:
        """Reveal multiple cells"""
        game = self.games[ctx.author.id]
        revealed: GameBoard = game["revealed"]
        board: GameBoard = game["board"]

        reload_board = True
        for x, y in cords:
            if not await self.reveal_one(ctx, revealed, board, x, y):
                reload_board = False
        if reload_board:
            await self.reload_board(ctx)

    @commands.command(name="end")
    async def end_command(self, ctx: commands.Context):
        """End the current game"""
        game = self.games[ctx.author.id]
        game["revealed"] = game["board"]
        await self.reload_board(ctx)
        await ctx.author.send(":no_entry: you canceled the game :no_entry:")
        await game["chat_msg"].channel.send(f"{ctx.author.mention} just canceled Minesweeper.")
        del self.games[ctx.author.id]


def setup(bot: commands.Bot) -> None:
    """Cog load."""
    bot.add_cog(Minesweeper(bot))

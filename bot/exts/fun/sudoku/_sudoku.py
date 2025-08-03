import asyncio
import os
# from asyncio import TimeoutError
from typing import Optional
import random
import time
import io
import enum
from ._board_generation import GenerateSudokuPuzzle

import discord
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

BACKGROUND = (242, 243, 244)
BLACK = 0
SUDOKU_TEMPLATE_PATH = "bot/resources/fun/sudoku_template.png"
NUM_FONT = ImageFont.truetype("bot/resources/fun/Roboto-Medium.ttf", 80)


class CoordinateConverter(commands.Converter):
    """Converter used in Sudoku game."""
    async def convert(self, argument: str) -> tuple[int, int]:
        """Convert alphanumeric grid coordinates to 2d list index. Eg 'C1'-> (2, 0)."""
        argument = sorted(argument.lower())
        if len(argument) != 2:
            raise commands.BadArgument("The coordinate must be two characters long.")
        if argument[0].isnumeric() and not argument[1].isnumeric():
            number, letter = argument[0], argument[1]
        else:
            raise commands.BadArgument("The coordinate must comprise of"
                                       "1 letter from A to F, and 1 number from 1 to 6.")
        if 0 > int(number) > 10 or letter not in "abcdef":
            raise commands.BadArgument("The coordinate must comprise of"
                                       "1 letter from A to F, and 1 number from 1 to 6.")
        return ord(letter)-97, int(number)-1


# class Difficulty(enum.Enum):
#     """Class for enumerating the difficulty of the Sudoku game."""
#
#     difficulties = {"easy": 1, "medium": 2, "hard": 3}
#     difficulty = random.choice(list(difficulties.values()))


class SudokuGame:
    """Class that contains information regarding the currently running Sudoku game."""

    def __init__(self, ctx: commands.Context):
        self.image = Image.open(SUDOKU_TEMPLATE_PATH)
        self.generate_puzzle()
        self.running: bool = True
        self.invoker: discord.Member = ctx.author
        self.started_at = time.time()

    def draw_num(self, digit: int, position: tuple[int, int]) -> Image:
        """Draw a number on the Sudoku board."""
        digit = str(digit)
        if digit in "123456" and len(digit) == 1:
            draw = ImageDraw.Draw(self.image)
            draw.text(self.index_to_coord(position), str(digit), fill=BLACK, font=NUM_FONT)
            return self.image

    @staticmethod
    def index_to_coord(position: tuple[int, int]) -> tuple[int, int]:
        """Convert a 2D list index to an x,y coordinate on the Sudoku image."""
        return position[0] * 83 + 100, (position[1]) * 83 + 11

    @classmethod
    def generate_puzzle(cls):
        """Generate a valid Sudoku board."""
        generate_puzzle = GenerateSudokuPuzzle()
        generate_puzzle.generate_solution()
        generate_puzzle.remove_numbers_from_grid()

    @property
    def solved(self) -> bool:
        """Check if the puzzle has been solved."""
        return self.solution == self.puzzle

    def num_concat(self, num1, num2):
        num1 = str(num1)
        num2 = str(num2)
        num1 += num2
        return num1

    def time_convert(self, secs):
        mins = secs // 60
        secs = secs % 60
        mins = mins % 60
        if secs < 10:
            secs_2 = self.num_concat(0, int(float(secs)))
            formatted_time = "{0}:{1}".format(int(mins), secs_2)
        else:
            formatted_time = "{0}:{1}".format(int(mins), int(secs))

        return formatted_time


class Sudoku(commands.Cog):
    """Cog for the Sudoku game."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.games: dict[int, SudokuGame]
        self.started_at = time.time()
        self.ctx = ctx
        self.hints: list[time.time] = []
        self.message = None

    async def timer_embed(self, ctx: commands.Context):
        current_time = time.time()
        time_elapsed = current_time - self.started_at
        formatted_time = self.time_convert(time_elapsed)
        timer_message = discord.Embed(title="Time Elapsed:", description=formatted_time, color=Colours.blue)
        send_timer = await ctx.send(embed=timer_message)

        game = self.games.get(ctx.author.id)
        while game:
            await asyncio.sleep(1)
            current_time = time.time()
            time_elapsed = current_time - self.started_at
            formatted_time = self.time_convert(time_elapsed)
            timer_message.description = formatted_time
            await send_timer.edit(embed=timer_message)

            # if coord and digit.isnumeric() and -1 < int(digit) < 10 or digit in "xX":
            #     # print(f"{coord=}, {digit=}")
            #     await game.update_board(digit, coord)
            # else:
            #     raise commands.BadArgument

            # while game is in progress:
            # print(timer_message)

    def info_embed(self) -> discord.Embed:
        """Create an embed that displays game information."""
        # current_time = time.time()
        # time_elapsed = current_time - self.started_at
        # formatted_time = self.time_convert(time_elapsed)
        info_embed = discord.Embed(title="Sudoku Game Information", color=Colours.grass_green)
        info_embed.set_author(name=self.invoker.name, icon_url=self.invoker.display_avatar.url)
        # info_embed.add_field(name="Current Time (mins:secs)", value=formatted_time)
        info_embed.add_field(name="Difficulty", value=self.difficulty, inline=False)
        info_embed.add_field(name="Hints Used", value=len(self.hints), inline=False)
        info_embed.add_field(name="Progress", value="N/A", inline=False)  # add in this variable
        return info_embed

    async def update_board(self, digit=None, coord=None):
        sudoku_embed = discord.Embed(title="Sudoku", color=Colours.soft_orange)
        if digit and coord:
            self.draw_num(digit, coord)
        board_image = io.BytesIO(b"sudoku.png: \x00\x01")
        sudoku_embed.set_image(board_image)
        if self.message:
            await self.message.delete()
        self.message = await self.ctx.send(file=board_image, embed=sudoku_embed, view=SudokuView(self.ctx))

    def find_empty_square(self, grid):
        """Return the next empty square coordinates in the grid."""
        for i in range(6):
            for j in range(6):
                if grid[i][j] == 0:
                    return i, j
        return

    @commands.group(aliases=["s"], invoke_without_command=True)
    async def sudoku(self, ctx: commands.Context) -> None:
        """
        Play Sudoku with the bot!

        Sudoku is a grid game where you start with a 9x9 grid, and you are given certain numbers on the
        grid. In this version of the game, however, the grid will be a 6x6 one instead of the traditional
        9x9. In the original game, all numbers on the grid are 1-9, and no number can repeat itself in any row,
        column, or any of the smaller 3x3 grids. In this version of the game, there are 2x3 smaller grids
        instead of 3x3 and numbers 1-6 will be used on the grid.
        """
        game = self.games.get(ctx.author.id)
        if not game:
            await ctx.send("Welcome to Sudoku! Type your guesses like this: `A1 1`")
            timer_embed()

            await self.timer_embed(ctx)
            await self.start(ctx)
            await self.bot.wait_for(event="message")

    @sudoku.command()
    async def start(self, ctx: commands.Context, difficulty: str = "Normal") -> None:
        """Start a Sudoku game."""
        if self.games.get(ctx.author.id):
            await ctx.send("You are already playing a game!")
            return
        game = self.games[ctx.author.id] = SudokuGame(ctx, difficulty)
        await game.update_board()

    @sudoku.command(aliases=["end", "stop"])
    async def finish(self, ctx: commands.Context) -> None:
        """End a Sudoku game."""
        game = self.games.get(ctx.author.id)
        if game:
            if ctx.author == game.invoker:
                del self.games[ctx.author.id]
                await ctx.send("Ended the current game.")
            else:
                await ctx.send("Only the owner of the game can end it!")
        else:
            await ctx.send("You are not playing a game! Type `.s` to begin.")

    @sudoku.command()
    async def info(self, ctx: commands.Context) -> None:
        """Send info about a currently running Sudoku game."""
        game = self.games.get(ctx.author.id)
        if game:
            await ctx.send(embed=game.info_embed())
        else:
            await ctx.send("This game has ended! Type `.s` to start a new game.")

    @sudoku.command()
    async def hint(self, ctx: commands.Context) -> None:
        """Fill in one empty square on the Sudoku board."""
        game = self.games.get(ctx.author.id)
        if game:
            game.hints.append(time.time())
            while True:
                empty_coords = self.find_empty_square(game.puzzle)
                empty_coords_list = [empty_coords]

                await game.update_board(digit=random.randint(0, 5), coord=random.choice(empty_coords_list))
                break


class SudokuView(discord.ui.View):
    """A set of buttons to control a Sudoku game."""

    @discord.ui.button(style=discord.ButtonStyle.green, label="Hint")
    async def hint_button(self, *_) -> None:
        """Button that fills in one empty square on the Sudoku board."""
        await self.ctx.invoke(self.ctx.bot.get_command("sudoku hint"))

    @discord.ui.button(style=discord.ButtonStyle.primary, label="Game Info")
    async def info_button(self, *_) -> None:
        """Button that displays information about the current game."""
        await self.ctx.invoke(self.ctx.bot.get_command("sudoku info"))

    @discord.ui.button(style=discord.ButtonStyle.red, label="End Game")
    async def end_button(self, *_) -> None:
        """Button that ends the current game."""
        await self.ctx.invoke(self.ctx.bot.get_command("sudoku finish"))
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check to ensure that the interacting user is the user who invoked the command."""
        if interaction.user != self.ctx.author:
            error_embed = discord.Embed(
                description="Sorry, but this button can only be used by the original author.")
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return False
        return True


def setup(bot: Bot) -> None:
    """Load the Sudoku cog."""
    bot.add_cog(Sudoku(bot))

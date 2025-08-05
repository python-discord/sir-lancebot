import os
from typing import Optional
import random
import time

import discord
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

from ._board_generation import GenerateSudokuPuzzle

BACKGROUND = (242, 243, 244)
BLACK = 0
SUDOKU_TEMPLATE_PATH = "bot/resources/fun/sudoku_template.png"
NUM_FONT = ImageFont.truetype("bot/resources/fun/Roboto-Medium.ttf", 99)


class CoordinateConverter(commands.Converter):
    """Converter used in Sudoku game."""

    async def convert(self, ctx: commands.Context, argument: str) -> tuple[int, int]:
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


class SudokuGame:
    """Class that contains information and regarding Sudoku game."""

    def __init__(self, ctx: commands.Context, difficulty: str):
        self.ctx = ctx
        self.image = Image.open(SUDOKU_TEMPLATE_PATH)
        self.solution = self.generate_board()
        self.puzzle = self.generate_puzzle()
        self.running: bool = True
        self.invoker: discord.Member = ctx.author
        self.started_at = time.time()
        self.difficulty: str = difficulty  # enum class?
        self.hints: list[time.time] = []
        self.message = None

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

    @staticmethod
    def generate_board() -> tuple[list[list[int]], list[list[int]]]:
        """Generate a valid Sudoku puzzle."""
        return GenerateSudokuPuzzle().generate_puzzle()

    def generate_puzzle(self) -> list[list[int]]:
        """Remove numbers from a valid Sudoku solution based on the difficulty. Returns a Sudoku puzzle."""
        self.puzzle = [([0]*6)]*6
        return self.puzzle

    @property
    def solved(self) -> bool:
        """Check if the puzzle has been solved."""
        return self.solution == self.puzzle

    def info_embed(self) -> discord.Embed:
        """Create an embed that displays game information."""
        current_time = time.time()
        info_embed = discord.Embed(title="Sudoku Game Information", color=Colours.grass_green)
        info_embed.add_field(name="Player", value=self.invoker.name)
        info_embed.add_field(name="Current Time", value=(current_time - self.started_at))
        info_embed.add_field(name="Progress", value="N/A")  # add in this variable
        info_embed.add_field(name="Difficulty", value=self.difficulty)
        info_embed.set_author(name=self.invoker.name, icon_url=self.invoker.display_avatar.url)
        info_embed.add_field(name="Hints Used", value=len(self.hints))
        return info_embed

    async def update_board(self, digit=None, coord=None):
        sudoku_embed = discord.Embed(title="Sudoku", color=Colours.soft_orange)
        if digit and coord:
            self.draw_num(digit, coord)
        self.image.save("sudoku.png")
        board_image = discord.File("sudoku.png")
        sudoku_embed.set_image(url="attachment://sudoku.png")
        if self.message:
            await self.message.delete()
        self.message = await self.ctx.send(file=board_image, embed=sudoku_embed, view=SudokuView(self.ctx))
        os.remove("sudoku.png")


class Sudoku(commands.Cog):
    """Cog for the Sudoku game."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.games: dict[int, SudokuGame] = {}

    @commands.group(aliases=["s"], invoke_without_command=True)
    async def sudoku(self, ctx: commands.Context, coord: Optional[CoordinateConverter] = None,
                     digit: Optional[str] = None) -> None:
        """
        Play Sudoku with the bot!

        Sudoku is a grid game where you start with a 9x9 grid, and you are given certain numbers on the
        grid. In this version of the game, however, the grid will be a 6x6 one instead of the traditional
        9x9. All numbers on the grid, traditionally, are 1-9, and no number can repeat itself in any row,
        column, or any of the smaller 3x3 grids. In this version of the game, it would be 2x3 smaller grids
        instead of 3x3 and numbers 1-6 will be used on the grid.
        """
        game = self.games.get(ctx.author.id)
        if not game:
            await ctx.send("Welcome to Sudoku! Type your guesses like so: `A1 1`")
            await self.start(ctx)
            await self.bot.wait_for("message")
            if coord and digit.isnumeric() and -1 < int(digit) < 10 or digit in "xX":
                # print(f"{coord=}, {digit=}")
                await game.update_board(digit, coord)
            else:
                raise commands.BadArgument

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
            await ctx.send("You are not playing a Sudoku game! Type `.sudoku start` to begin.")

    @sudoku.command(aliases=["who", "information", "score"])
    async def info(self, ctx: commands.Context) -> None:
        """Send info about a currently running Sudoku game."""
        game = self.games.get(ctx.author.id)
        if game:
            await ctx.send(embed=game.info_embed())
        else:
            await ctx.send("You are not playing a game!")

    @sudoku.command()
    async def hint(self, ctx: commands.Context) -> None:
        """Fill in one empty square on the Sudoku board."""
        game = self.games.get(ctx.author.id)
        if game:
            game.hints.append(time.time())
            while True:
                x, y = random.randint(0, 5), random.randint(0, 5)
                if game.puzzle[x][y] == 0:
                    await game.update_board(digit=random.randint(0, 5), coord=(x, y))
                    break


class SudokuView(discord.ui.View):
    """A set of buttons to control a Sudoku game."""

    def __init__(self, ctx: commands.Context):
        super(SudokuView, self).__init__()
        self.disabled = None
        self.ctx = ctx
        # self.children[0]

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

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check to ensure that the interacting user is the user who invoked the command."""
        if interaction.user != self.ctx.author:
            error_embed = discord.Embed(
                description="Sorry, but this button can only be used by the original author.")
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return False
        return True


async def setup(bot: Bot) -> None:
    """Load the Sudoku cog."""
    await bot.add_cog(Sudoku(bot))

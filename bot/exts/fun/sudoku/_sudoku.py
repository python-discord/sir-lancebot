import asyncio
import random
import re
from random import choice

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES

from ._sudoku_grid import SudokuDifficulty, SudokuGrid

BLUE = (0, 0, 255)
RED = (255, 0, 0)


class SudokuGame:
    """Class that contains helper methods for a Sudoku game."""

    def __init__(self, ctx: commands.Context, difficulty: SudokuDifficulty, cog: "Sudoku"):
        self.grid = SudokuGrid(difficulty)

        self.cog: Sudoku = cog
        self.invoker: discord.Member = ctx.author
        self.channel = ctx.channel
        self.message: discord.Message | None = None
        self.view: SudokuView | None = None

        self.hints: int = 0
        self.correct: int = 0
        self.incorrect: int = 0
        self.wait_task: asyncio.Task | None = None

    async def send_or_update_message(self) -> None:
        # Create embed
        embed_description = (
            f"Hints used: {self.hints} / 5\n"
            f"Correct / incorrect guesses: {self.correct} / {self.incorrect}"
        )
        embed = discord.Embed(title="Sudoku", color=Colours.soft_orange, description=embed_description)
        embed.set_image(url="attachment://sudoku.png")
        file = self.grid.image_as_discord_file()

        if self.message is None:
            self.view = SudokuView(self)
            self.message = await self.channel.send(embed=embed, file=file, view=self.view)
        else:
            await self.message.edit(embed=embed, attachments=[file], view=self.view)

    async def guess(self, coord: tuple[int, int], digit: int, message: discord.Message) -> None:
        result = self.grid.guess(coord, digit)
        if not result:
            self.incorrect += 1
            await message.add_reaction("❌")
            return

        self.correct += 1
        await message.add_reaction("✅")

        await self.check_solved()
        await self.send_or_update_message()

    def get_hint(self) -> tuple[int, int]:
        self.hints += 1

        # Update internal board
        x, y = random.choice(list(self.grid.empty_squares))
        self.grid.guess((x, y), self.grid.solution[x][y], BLUE)

        if self.hints > 5:
            self.view.hint_button.disabled = True

        return x, y

    async def check_solved(self) -> None:
        if self.grid.is_solved():
            self.view.stop()
            self.view = None

            await self.channel.send("Congratulations! You solved the puzzle!")
            self.end_game()

    def end_game(self) -> None:
        # Cancel the wait task if it's running
        if self.wait_task is not None and not self.wait_task.done():
            self.wait_task.cancel()

        self.view.stop()
        for child in self.view.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

        # Fill in empty squares (if game was aborted)
        for x, row in enumerate(self.grid.solution):
            for y, digit in enumerate(row):
                self.grid.guess((x, y), digit, RED)

        # Remove game from registry
        self.cog.games.pop(self.invoker.id)


class Sudoku(commands.Cog):
    """Cog for the Sudoku game."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.games: dict[int, SudokuGame] = {}

    @commands.command()
    async def sudoku(self, ctx: commands.Context, difficulty: str | None) -> None:
        """
        Play Sudoku with the bot!

        Sudoku is a grid game where you start with a 9x9 grid, and you are given certain numbers on the
        grid. In this version of the game, however, the grid will be a 6x6 one instead of the traditional
        9x9. All numbers on the grid, traditionally, are 1-9, and no number can repeat itself in any row,
        column, or any of the smaller 3x3 grids. In this version of the game, it would be 2x3 smaller grids
        instead of 3x3 and numbers 1-6 will be used on the grid.
        """
        if ctx.author.id in self.games:
            await ctx.send("You are already playing a game!")
            return

        if not difficulty:
            await ctx.send("Please specify a difficulty: `.sudoku easy/normal/hard`")
            return

        difficulty_arg = self.parse_difficulty(difficulty)
        if not difficulty_arg:
            await ctx.send("Invalid difficulty! Choose from: easy, normal, hard.")
            return

        await ctx.send("Welcome to Sudoku! Type your guesses like so: `A1 1`\n"
                       "Note: Hints are marked in blue, guesses are marked in red.")

        game = SudokuGame(ctx, difficulty_arg, self)
        await game.send_or_update_message()
        self.games[ctx.author.id] = game

        def is_valid(msg: discord.Message) -> bool:
            return msg.author == ctx.author and msg.channel == ctx.channel

        game.wait_task = asyncio.create_task(
            self.bot.wait_for("message", timeout=120, check=is_valid)
        )
        try:
            await game.wait_task
        except TimeoutError:
            timeout_embed = discord.Embed(
                title=choice(NEGATIVE_REPLIES),
                description="Uh oh! You took too long to respond!",
                color=Colours.soft_red,
            )
            await ctx.send(ctx.author.mention, embed=timeout_embed)
            game.end_game()
            await game.send_or_update_message()
            return

    @staticmethod
    def parse_difficulty(diff: str) -> SudokuDifficulty | None:
        diff = diff.lower()
        if diff == "easy":
            return "easy"
        if diff == "normal":
            return "normal"
        if diff == "hard":
            return "hard"
        return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if (game := self.games.get(message.author.id)) is None:
            return
        if (match := re.match(r"^([a-z])([1-6]) ([1-6])$", message.content.lower())) is None:
            return

        col_str, row_str, digit_str = match.groups()
        col = ord(col_str) - ord("a")
        row = int(row_str) - 1
        digit = int(digit_str)

        await game.guess((row, col), digit, message)


class SudokuView(discord.ui.View):
    """A set of buttons to control a Sudoku game."""

    def __init__(self, game: SudokuGame):
        super().__init__(timeout=120)
        self.game = game

    @discord.ui.button(style=discord.ButtonStyle.green, label="Hint")
    async def hint_button(self, interaction: discord.Interaction, *_) -> None:
        """Button that fills in one empty square on the Sudoku board."""
        if self.game.hints > 5:
            await interaction.response.send_message("You ran out of hints!", ephemeral=True)

            await interaction.followup.edit_message(message_id=interaction.message.id, view=self)
            return

        row, col = self.game.get_hint()

        cols = "ABCDEF"
        rows = "123456"
        await interaction.response.send_message(f"Hint placed at {cols[col]}{rows[row]}.", ephemeral=True)

        await self.game.check_solved()
        await self.game.send_or_update_message()

    @discord.ui.button(style=discord.ButtonStyle.red, label="End Game")
    async def end_button(self, interaction: discord.Interaction, *_) -> None:
        """Button that ends the current game."""
        if interaction.user == self.game.invoker:
            self.game.end_game()
            await interaction.response.send_message("Ended the current game.", ephemeral=True)
            await self.game.send_or_update_message()
        else:
            await interaction.response.send_message("Only the owner of the game can end it!", ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check to ensure that the interacting user is the user who invoked the command."""
        if interaction.user != self.game.invoker:
            await interaction.response.send_message(
                "Sorry, but this button can only be used by the original author.", ephemeral=True)
            return False
        return True


async def setup(bot: Bot) -> None:
    """Load the Sudoku cog."""
    await bot.add_cog(Sudoku(bot))

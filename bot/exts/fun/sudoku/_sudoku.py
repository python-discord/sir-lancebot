import asyncio
import io
import random
from random import choice

import discord
from PIL import Image
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES

from ._sudoku_grid import SudokuDifficulty, SudokuGrid


class SudokuGame:
    """Class that contains helper constants for a Sudoku game."""

    def __init__(self, ctx: commands.Context, difficulty: SudokuDifficulty, cog: "Sudoku"):
        self.ctx = ctx
        self.cog = cog
        self.grid = SudokuGrid(difficulty)
        self.hints: int = 0
        self.image = self.grid.image
        self.board = [row[:] for row in self.grid.puzzle]
        self.invoker: discord.Member = ctx.author
        self.message: discord.Message | None = None


class Sudoku(commands.Cog):
    """Cog for the Sudoku game."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.games: dict[int, SudokuGame] = {}

    @staticmethod
    def is_valid_guess_format(content: str) -> bool:
        parts = content.strip().upper().split()
        if len(parts) != 2:
            return False
        coord, digit = parts
        if len(coord) != 2 or coord[0] not in "ABCDEF" or not coord[1].isdigit():
            return False
        return (digit.isdigit() and 1 <= int(digit) <= 6) or digit in "Xx"

    @staticmethod
    def pil_to_discord_file(image: Image.Image, filename: str = "sudoku.png") -> discord.File:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return discord.File(buffer, filename=filename)

    @commands.command()
    async def sudoku(self, ctx: commands.Context, difficulty: SudokuDifficulty = "normal") -> None:
        """
        Play Sudoku with the bot!

        Sudoku is a grid game where you start with a 9x9 grid, and you are given certain numbers on the
        grid. In this version of the game, however, the grid will be a 6x6 one instead of the traditional
        9x9. All numbers on the grid, traditionally, are 1-9, and no number can repeat itself in any row,
        column, or any of the smaller 3x3 grids. In this version of the game, it would be 2x3 smaller grids
        instead of 3x3 and numbers 1-6 will be used on the grid.
        """
        diff = difficulty.lower()

        valid_difficulties: tuple[SudokuDifficulty, ...] = ("easy", "normal", "hard")
        if diff not in valid_difficulties:
            await ctx.send("Invalid difficulty! Choose from: easy, normal, hard.")
            return

        game = self.games.get(ctx.author.id)
        if game:
            await ctx.send("You are already playing a game!")
            return

        game = SudokuGame(ctx, difficulty, self)
        self.games[ctx.author.id] = game

        def is_valid(msg: ctx.message) -> bool:
            return msg.author == ctx.author and msg.channel == ctx.channel

        view = SudokuView(ctx, self)
        game = self.games.get(ctx.author.id)
        await ctx.send("Welcome to Sudoku! Type your guesses like so: `A1 1`\n"
                       "Note: Hints are marked in blue, guesses are marked in red.\n"
                       "Hints allowed: Easy: 6; Normal: 4; Hard: 2")
        sudoku_embed = discord.Embed(title="Sudoku", color=Colours.soft_orange)
        file = self.pil_to_discord_file(game.image)
        sudoku_embed.set_image(url="attachment://sudoku.png")
        game.message = await ctx.send(embed=sudoku_embed, file=file, view=view)

        game.wait_task = asyncio.create_task(
            self.bot.wait_for("message", timeout=120, check=is_valid)
        )
        try:
            await game.wait_task
        except TimeoutError:
            timeout_embed = discord.Embed(
                title=choice(NEGATIVE_REPLIES),
                description="Uh oh! You took too long to respond!",
                color=Colours.soft_red
            )

            await ctx.send(ctx.author.mention, embed=timeout_embed)

            view.stop()
            for child in view.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True

            await game.message.edit(view=view)
            return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        game = self.games.get(message.author.id)
        if not game or not game.message:
            return

        content = message.content.strip().upper()
        if not self.is_valid_guess_format(content):
            return  # ignore invalid formats

        coord_str, digit_str = message.content.strip().split()
        col_letter, row_number = coord_str[0], coord_str[1:]
        row = int(row_number) - 1  # e.g. "2" → 1 (0-indexed)
        col = ord(col_letter.upper()) - ord("A")  # "D" → 3

        coord = (row, col)
        digit = int(digit_str)

        if game.grid.guess(coord, digit):
            game.grid.draw_digit(coord, digit, (255, 0, 0))

            # Convert image to discord.File
            file = self.pil_to_discord_file(game.grid.image)

            # Create updated embed
            embed = discord.Embed(title="Sudoku", color=Colours.soft_orange)
            embed.set_image(url="attachment://sudoku.png")

            # Edit the original message
            await game.message.edit(embed=embed, attachments=[file], view=SudokuView(game.ctx, self))

            if game.grid.is_solved():
                await game.ctx.send("Congratulations! You solved the puzzle!")
        else:
            await message.add_reaction("❌")


class SudokuView(discord.ui.View):
    """A set of buttons to control a Sudoku game."""

    def __init__(self, ctx: commands.Context, cog: Sudoku):
        super().__init__(timeout=120)
        self.disabled = None
        self.ctx = ctx
        self.cog = cog

    @discord.ui.button(style=discord.ButtonStyle.green, label="Hint")
    async def hint_button(self, interaction: discord.Interaction, *_) -> None:
        """Button that fills in one empty square on the Sudoku board."""
        game = self.cog.games.get(interaction.user.id)
        if not game:
            await interaction.response.send_message("You're not playing a game!", ephemeral=True)
            return
        game.hints += 1
        # Find an empty cell and fill it with the correct value
        empty_cells = [(i, j) for i in range(6) for j in range(6) if game.grid.puzzle[i][j] == 0]
        if not empty_cells:
            await interaction.response.send_message("No empty cells left to hint.", ephemeral=True)
            return

        # Update internal board
        x, y = random.choice(empty_cells)
        game.grid.puzzle[x][y] = game.grid.solution[x][y]
        game.grid.empty_squares.discard((x, y))

        # Draw the digit
        game.grid.draw_digit((x, y), game.grid.solution[x][y], (0, 0, 255))
        await interaction.response.send_message(f"Hint placed at {chr(65 + y)}{x+1}.", ephemeral=True)

        file = self.cog.pil_to_discord_file(game.grid.image)

        embed = discord.Embed(title="Sudoku", color=Colours.soft_orange)
        embed.set_image(url="attachment://sudoku.png")

        if ((game.hints >= 6 and game.grid.difficulty == "easy") or
                (game.hints >= 4 and game.grid.difficulty == "normal") or
                (game.hints >= 2 and game.grid.difficulty == "hard")):
            # await interaction.response.send_message("You ran out of hints!", ephemeral=True)
            for child in self.children:
                if isinstance(child, discord.ui.Button) and child.label == "Hint":
                    child.disabled = True

        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            attachments=[file],
            embed=embed,
            view=self
        )

    @discord.ui.button(style=discord.ButtonStyle.red, label="End Game")
    async def end_button(self, interaction: discord.Interaction, *_) -> None:
        """Button that ends the current game."""
        game = self.cog.games.get(interaction.user.id)
        if game:
            if interaction.user == game.invoker:
                del self.cog.games[interaction.user.id]

                # Cancel the wait task if it's running
                wait_task = game.wait_task if hasattr(game, "wait_task") else None
                if wait_task and not wait_task.done():
                    wait_task.cancel()

                # Disable all buttons in the view
                for child in self.children:
                    if isinstance(child, discord.ui.Button):
                        child.disabled = True

                await interaction.response.send_message("Ended the current game.", ephemeral=True)
                await interaction.followup.edit_message(message_id=interaction.message.id, view=self)
            else:
                await interaction.response.send_message("Only the owner of the game can end it!", ephemeral=True)
        else:
            await interaction.response.send_message("You are not playing a Sudoku game! Type `.sudoku` to "
                                                    "begin.", ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check to ensure that the interacting user is the user who invoked the command."""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "Sorry, but this button can only be used by the original author.", ephemeral=True)
            return False
        return True


async def setup(bot: Bot) -> None:
    """Load the Sudoku cog."""
    await bot.add_cog(Sudoku(bot))

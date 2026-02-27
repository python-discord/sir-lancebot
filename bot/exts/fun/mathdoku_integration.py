import asyncio
import re
from random import choice


import discord
from discord.ext import commands
from pydis_core.utils.logging import get_logger

from copy import deepcopy

from bot.bot import Bot

CROSS_EMOJI = "\u274c"  # "\u274e"
MAGNIFYING_EMOJI = "🔍"
PARTY_EMOJI = "🎉"
HINT_EMOJI = "💡"
RULE_EMOJI = '📕'
mathdoku_rules = """Rules for Playing Mathdoku

The numbers you can enter on the board depend on the size of the board you selected. If you choose an n × n
board, you may use the numbers 1, 2, …, n. For example, on a 3 × 3 board you can use the numbers 1, 2, and 3.

The board is divided into cages, which are groups of squares outlined with a thick border. In the top-left
corner of each cage, a target number and a mathematical operation (+, −, ×, ÷) are shown. The numbers you
place in that cage must combine (using the indicated operation) to produce the target number. The operation
may be applied in any order.

Also note the following rules:

1. A number may appear at most once in each row and at most once in each column.
2. A cage with one square must contain the target number shown in its corner.
3. A number may be repeated within a cage, as long as the repeats are not in the same row or column.

The emojis attached to the board have different functions as well:

🔍 Check: This emoji only appears when the board is full. When pressed, it checks whether the board's conditions are fulfilled. If they are, the board turns green and a victory message is shown. If not, the cages that are not fulfilled turn red.

💡 Hint: This emoji provides a helpful hint to assist the player in solving the puzzle. It has a cooldown of 3 minutes.

📕 Rules: This emoji displays the rules of the Mathdoku game.
"""

log = get_logger(__name__)


class Mathdoku(commands.Cog):
    """Play a game of Mathdoku."""

    def __init__(self, bot: Bot, grids: dict):
        self.bot = bot
        self.grids = grids  # All possible game grids
        self.grid = None  # the currently active game grid
        self.playing = False
        self.player_id = None
        self.board = None  # The message that the board is posten on
        self.guess_count = 0
        self.rules_msg_exists = False
        self.rules_msg = None

    @commands.group(name="Mathdoku", aliases=("md",), invoke_without_command=True)
    async def mathdoku_group(self, ctx: commands.Context) -> None:
        """Commands for Playing Mathdoku."""
        await ctx.send("The Mathdoku API is working!")
        await self.bot.invoke_help_command(ctx)

    @mathdoku_group.command(name="start")
    async def start_command(self, ctx: commands.Context, size: int = 5, difficulty = "medium") -> None:
        """Start a game of Mathdoku
        size = the board size. Pick from 3-9
        difficulty = easy, medium or hard
        """

        size = int(size)
        difficulty = str(difficulty).lower()

        if self.playing:
            await ctx.send("Someone else is playing right now. Please wait your turn.")
            return

        if size not in [3,4,5,6,7,8,9]:
            await ctx.send("Please give a valid size between 3 and 9")
            return
        
        if difficulty not in ["easy", "medium", "hard"]:
            await ctx.send("Please give a valid difficulty: easy, medium or hard")
            return
    
        grids_available = self.grids[size][difficulty]
        if len(grids_available) < 1:
            await ctx.send("Couldn't find any boards for size: " + size + " and difficulty: " + difficulty  + ". Sorry :/")
            return
        
        self.playing = True
        self.player_id = ctx.author.id
        self.grid = deepcopy(choice(grids_available))  # get a random grid from the available ones for this size / difficulty
        await ctx.send("Game of Mathdoku has been started!")
        await ctx.send(
            "Press 🔍 to check if the board's conditions are met (only appears when the board is full)\n" 
            "Press 💡 to get a helpful hint on how to solve the puzzle\n"
            "Press 📕 to get the rules of the Mathdoku game")

        file = discord.File(self.grid._generate_image(), filename="mathdoku.png")
        self.board = await ctx.send(file=file)

        await ctx.send(
            "Type the square and what number you want to input. Format it like this: A1 3\nType `end` to end game."
        )

        await self.board.add_reaction(RULE_EMOJI)
        await self.board.add_reaction(HINT_EMOJI)

        while self.playing is True:
            await self.input_number_on_board(ctx)
        await ctx.send("Game of Mathdoku is over!")

    async def input_number_on_board(
        self,
        ctx: commands.Context,
    ) -> None:  # None might need to be changed later
        """Lets the player choose a square and input a number if it is valid."""
        msg_task = asyncio.create_task(self.bot.wait_for("message", check=self.predicate, timeout=60.0))
        react_task = asyncio.create_task(self.bot.wait_for("reaction_add", check=self.reaction_predicate, timeout=60.0))

        done, pending = await asyncio.wait({msg_task, react_task}, timeout=60.0, return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel()

        try:
            finished = done.pop()
            result = await finished

        except TimeoutError:  # Timeout
            await ctx.send("You took too long. Game over!")
            self.playing = False
            return
        
        except Exception:
            return

        if not self.playing:  # takes care of the end message
            await ctx.send("The game has been ended")
            return

        if finished is react_task:  # A Reaction was posted
            reaction, user = result
            emoji = str(reaction.emoji)
            if self.player_id != user.id:  # reaction by wrong player
                await self.board.remove_reaction(emoji, user)
            if self.rules_msg_exists:
                await self.rules_msg.delete()
                self.rules_msg_exists = False
                self.rules_msg = None
            if emoji == MAGNIFYING_EMOJI:
                await self.magnifying_handler(ctx=ctx, user=user)
            elif emoji == HINT_EMOJI:
                await self.hint_handler(ctx=ctx, user=user)
            elif emoji == RULE_EMOJI:
                await self.rules_handler(ctx=ctx, user=user)
            else:  # any other emoji
                await self.board.remove_reaction(emoji, user)

        else:  # A message was posted
            input_text = result.content.strip()
            valid_match = self.grid.add_guess(input_text)  # checks if its a valid guess and applies
            if not valid_match:
                await result.add_reaction(CROSS_EMOJI)
                return
            if self.rules_msg_exists:
                await self.rules_msg.delete()
                self.rules_msg_exists = False
                self.rules_msg = None
            try:
                await result.delete()
            except Exception:
                self.guess_count += 1

            if self.guess_count > 10:  # re-send the grid after 10 guesses so the user doesn't need to scroll
                await self.resent_message(ctx=ctx)
                self.guess_count = 0

            full_grid = self.grid.check_full_grid()
            if full_grid:
                await self.board.add_reaction(MAGNIFYING_EMOJI)

            self.grid.recolor_blocks()
            file = discord.File(self.grid._generate_image(), filename="mathdoku.png")
            await self.board.edit(content=None, attachments=[file])
            return

    def predicate(self, message: discord.Message) -> bool:
        """Predicate checking if the message matches a guess or the word end."""
        if self.player_id == message.author.id:
            input_text = message.content.strip()

            if input_text.lower() == "end":
                self.playing = False
                return True

            match = re.fullmatch(r"[A-Ja-j](10|[1-9])\s+[1-9]", input_text)
            if not match:
                self.guess_count += 1
                self.bot.loop.create_task(message.add_reaction(CROSS_EMOJI))
                return False
            return True
        return False

    def reaction_predicate(self, reaction: discord.Reaction, user: discord.User) -> bool:
        """Predicate checking if the reaction was on the correct message."""
        if self.board.id == reaction.message.id:
            return True
        return None

    async def magnifying_handler(self, ctx, user) -> None:
        if self.grid.check_full_grid():
            await self.board.remove_reaction(MAGNIFYING_EMOJI, user)

            result = self.grid.board_filled_handler()  # check win and update img
            file = discord.File(self.grid._generate_image(), filename="mathdoku.png")
            await self.board.edit(content=None, attachments=[file])

            if result: # WIN
                await self.board.add_reaction(PARTY_EMOJI)
                await ctx.send(PARTY_EMOJI + " Congrats! You WON " + PARTY_EMOJI)
                self.playing = False
            return
        await self.board.remove_reaction(MAGNIFYING_EMOJI, user)

    async def hint_handler(self, ctx, user) -> None:
        """Handle hint request via 💡 reaction."""
        await self.board.remove_reaction(HINT_EMOJI, user)
        result = self.grid.hint()

        if result["type"] == "cooldown":
            await ctx.send(f"Hint on cooldown. Try again in {result['remaining_seconds']}s.")
        elif result["type"] == "all filled cells":
            await ctx.send("No empty cells left.")
        else:
            await ctx.send(f"Hint: {result['guess']}")

    async def rules_handler(self, ctx, user) -> None:
        """Handle rules request via 📕 reaction."""
        await self.board.remove_reaction(RULE_EMOJI, user)
        self.rules_msg = await ctx.send(mathdoku_rules)
        self.rules_msg_exists = True

    async def resent_message(self, ctx):
        await self.board.delete()
        self.grid.recolor_blocks()
        file = discord.File(self.grid._generate_image(), filename="mathdoku.png")
        self.board = await ctx.send(file=file)
        await self.board.add_reaction(HINT_EMOJI)
        await ctx.send(
            "Type the square and what number you want to input. Format it like this: A1 3\n"
            "Type `end` to end game."
        )

async def setup(bot: Bot) -> None:
    """Load the Mathdoku cog."""
    from .mathdoku_parser import create_grids

    try:
        grids = await asyncio.to_thread(create_grids)
    except Exception:
        log.exception("Failed to create Mathdoku grids during setup()")
        grids = []
    await bot.add_cog(Mathdoku(bot, grids))

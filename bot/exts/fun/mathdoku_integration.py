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

        file = discord.File(self.grid._generate_image(), filename="mathdoku.png")
        self.board = await ctx.send(file=file)

        await ctx.send(
            "Type the square and what number you want to input. Format it like this: A1 3\nType `end` to end game."
        )

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
            if emoji == MAGNIFYING_EMOJI:
                await self.magnifying_handler(ctx=ctx, user=user)
            elif emoji == HINT_EMOJI:
                await self.hint_handler(ctx=ctx, user=user)
            elif emoji == "rules":
                pass
            else:  # any other emoji
                await self.board.remove_reaction(emoji, user)

        else:  # A message was posted
            input_text = result.content.strip()
            valid_match = self.grid.add_guess(input_text)  # checks if its a valid guess and applies
            if not valid_match:
                await result.add_reaction(CROSS_EMOJI)
                return

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
            if result:  # WIN
                await self.board.add_reaction(PARTY_EMOJI)
                await ctx.send(PARTY_EMOJI + " Congrats! You WON " + PARTY_EMOJI)
                self.playing = False
            return
        self.bot.loop.create_task(self.board.remove_reaction(MAGNIFYING_EMOJI, user))

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

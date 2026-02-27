import asyncio
import re

import discord
from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.bot import Bot

# TODO remove this import when merging files
from bot.exts.fun.mathdoku import Block, Grid

# These 2 commands make the API not work for some reason if uncommented
# from .mathdoku_parser import create_grids
# grids = create_grids()

# TODO remove this testing Grid
testingGrid = Grid(3)
cell_one = testingGrid.cells[0][0]
cell_two = testingGrid.cells[0][1]
cell_three = testingGrid.cells[0][2]
cell_four = testingGrid.cells[1][0]
cell_five = testingGrid.cells[1][1]
cell_six = testingGrid.cells[1][2]
cell_seven = testingGrid.cells[2][0]
cell_eight = testingGrid.cells[2][1]
cell_nine = testingGrid.cells[2][2]
testBlock_1 = Block("A", "+", 6, cell_one)
testBlock_2 = Block("B", "+", 9, cell_four)
testBlock_3 = Block("C", "+", 3, cell_five)
testingGrid.blocks.append(testBlock_1)
testingGrid.blocks.append(testBlock_2)
testingGrid.blocks.append(testBlock_3)

cell_one.guess = 1
cell_three.guess = 3
cell_seven.guess = 2

cell_one.correct = 1
cell_two.correct = 2
cell_three.correct = 3
cell_four.correct = 3
cell_five.correct = 1
cell_six.correct = 2
cell_seven.correct = 2
cell_eight.correct = 3
cell_nine.correct = 1

testBlock_1.cells.append(cell_one)
testBlock_1.cells.append(cell_two)
testBlock_1.cells.append(cell_three)
cell_one.block = testBlock_1
cell_two.block = testBlock_1
cell_three.block = testBlock_1

testBlock_2.cells.append(cell_four)
testBlock_2.cells.append(cell_seven)
testBlock_2.cells.append(cell_eight)
testBlock_2.cells.append(cell_nine)
cell_four.block = testBlock_2
cell_seven.block = testBlock_2
cell_eight.block = testBlock_2
cell_nine.block = testBlock_2

testBlock_3.cells.append(cell_five)
testBlock_3.cells.append(cell_six)
cell_five.block = testBlock_3
cell_six.block = testBlock_3


CROSS_EMOJI = "\u274c"  # "\u274e"
MAGNIFYING_EMOJI = "🔍"
PARTY_EMOJI = "🎉"
HINT_EMOJI = "💡"
log = get_logger(__name__)
has_filled_board_prev = False


class Mathdoku(commands.Cog):
    """Play a game of Mathdoku."""

    def __init__(self, bot: Bot, grids: dict):
        self.bot = bot
        self.grids = grids  # The game Grid
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
    async def start_command(self, ctx: commands.Context, size: int = 5) -> None:
        """Start a game of Mathdoku."""

        if self.playing:
            await ctx.send("Someone else is playing right now. Please wait your turn.")
            return
        self.playing = True

        self.player_id = ctx.author.id
        await ctx.send("Game of Mathdoku has been started!")

        # TODO Create an actual Grid:
        self.grids = testingGrid
        file = discord.File(self.grids._generate_image(), filename="mathdoku.png")
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
            valid_match = self.grids.add_guess(input_text)  # checks if its a valid guess and applies
            if not valid_match:
                await result.add_reaction(CROSS_EMOJI)
                return

            self.guess_count += 1
            if self.guess_count % 10 == 0:  # re-send the grid after 10 guesses so the user doesn't need to scroll
                await self.board.delete()
                self.grids.recolor_blocks()
                file = discord.File(self.grids._generate_image(), filename="mathdoku.png")
                self.board = await ctx.send(file=file)
                await self.board.add_reaction(HINT_EMOJI)
                await ctx.send(
                    "Type the square and what number you want to input. Format it like this: A1 3\n"
                    "Type `end` to end game."
                )

            full_grid = self.grids.check_full_grid()
            if full_grid:
                await self.board.add_reaction(MAGNIFYING_EMOJI)

            self.grids.recolor_blocks()
            file = discord.File(self.grids._generate_image(), filename="mathdoku.png")
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
        if self.grids.check_full_grid():
            await self.board.remove_reaction(MAGNIFYING_EMOJI, user)

            result = self.grids.board_filled_handler()  # check win and update img
            file = discord.File(self.grids._generate_image(), filename="mathdoku.png")
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
        result = self.grids.hint()

        if result["type"] == "cooldown":
            await ctx.send(f"Hint on cooldown. Try again in {result['remaining_seconds']}s.")
        elif result["type"] == "all filled cells":
            await ctx.send("No empty cells left.")
        else:
            await ctx.send(f"Hint: {result['guess']}")


async def setup(bot: Bot) -> None:
    """Load the Mathdoku cog."""
    from .mathdoku_parser import create_grids

    try:
        grids = await asyncio.to_thread(create_grids)
    except Exception:
        log.exception("Failed to create Mathdoku grids during setup()")
        grids = []
    await bot.add_cog(Mathdoku(bot, grids))

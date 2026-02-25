import asyncio
from collections.abc import Iterator
from dataclasses import dataclass
from random import randint, random

import discord
from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import Client
from bot.utils.converters import CoordinateConverter
from bot.utils.exceptions import UserNotPlayingError
# TODO remove this import when merging files
from bot.exts.fun.mathdoku import Grid, Block 

import re


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


CROSS_EMOJI = '\u274C' #"\u274e"
MAGNIFYING_EMOJI = '🔍'
PARTY_EMOJI = "🎉"
log = get_logger(__name__)


class Mathdoku(commands.Cog):
    """Play a game of Mathdoku."""

    def __init__(self, bot: Bot, grids: list):
        self.bot = bot
        self.grids = grids # The game Grid
        self.playing = False
        self.player_id = None
        self.board = None # The message that the board is posten on

    @commands.group(name="Mathdoku", aliases=("md",), invoke_without_command=True)
    async def mathdoku_group(self, ctx: commands.Context) -> None:
        """Commands for Playing Mathdoku."""
        await ctx.send("The Mathdoku API is working!")
        await self.bot.invoke_help_command(ctx)

    @mathdoku_group.command(name="start")
    async def start_command(self, ctx: commands.Context, size: int = 5) -> None:
        """Start a game of Mathdoku."""
        self.player_id = ctx.author.id
        await ctx.send("Game of Mathdoku has been started!")

        # TODO Create an actual Grid:
        self.grids = testingGrid
        file = discord.File(self.grids._generate_image(), filename="mathdoku.png")
        self.board = await ctx.send(file=file)

        await ctx.send(
            "Type the square and what number you want to input. Format it like this: A1 3\n" "Type `end` to end game."
        )
        

        self.playing = True
        while self.playing == True:
            await self.input_number_on_board(ctx)

        await ctx.send("Game of Mathdoku is over!")

    async def input_number_on_board(self, ctx: commands.Context,) -> None:  # None might need to be changed later
        """Lets the player choose a square and input a number if it is valid."""
        
        msg_task = asyncio.create_task(self.bot.wait_for("message", check=self.predicate, timeout=60.0))
        react_task = asyncio.create_task(self.bot.wait_for("reaction_add", check=self.reaction_predicate, timeout=60.0))
        
        _, pending = await asyncio.wait({msg_task, react_task}, timeout=60.0, return_when = asyncio.FIRST_COMPLETED)
        
        for task in pending:
            task.cancel()

        try:
            pass    
            
        except TimeoutError:
            await ctx.send("You took too long. Game over!")
            self.playing = False
            return

        if not self.playing:
            await ctx.send("The game has been ended")
            return
        else:
            file = discord.File(self.grids._generate_image(), filename="mathdoku.png")
            await self.board.edit(content=None, attachments=[file])
            return

    def predicate(self, message: discord.Message) -> bool:
        """Predicate checking the message typed for each turn."""
        if self.player_id == message.author.id:
            input_text = message.content.strip()

            if input_text.lower() == "end":
                self.playing = False
                return True

            match = re.fullmatch(r"[A-Ja-j](10|[1-9])\s+[1-9]", input_text)
            if not match:
                self.bot.loop.create_task(message.add_reaction(CROSS_EMOJI))
                return bool(match)
            
            valid_match = self.grids.add_guess(input_text) # checks if its a valid guess and applies
            full_grid = self.grids.check_full_grid()
            if (full_grid):
                self.bot.loop.create_task(self.board.add_reaction(MAGNIFYING_EMOJI))
            # might wanna change to another format
            if not valid_match:
                self.bot.loop.create_task(message.add_reaction(CROSS_EMOJI))
            return valid_match
        else: 
            return False
        


    def reaction_predicate(self, reaction: discord.Reaction, user: discord.User) -> bool:
        """Predicate checking the reaction"""
        if self.player_id == user.id and self.board.id == reaction.message.id:
            emoji = str(reaction.emoji)
            if emoji == MAGNIFYING_EMOJI:
                if self.grids.check_full_grid():
                    result = self.grids.board_filled_handler()
                    self.bot.loop.create_task(self.board.remove_reaction(MAGNIFYING_EMOJI, user))
                    file = discord.File(self.grids._generate_image(), filename="mathdoku.png")
                    self.bot.loop.create_task(self.board.edit(content=None, attachments=[file]))
                    if result:
                        self.bot.loop.create_task(self.board.add_reaction(PARTY_EMOJI))
                    return result
                else:
                    self.bot.loop.create_task(self.board.remove_reaction(MAGNIFYING_EMOJI, user))
                return False
                
            else:
                self.bot.loop.create_task(self.board.remove_reaction(emoji, user))
                return False
        
            


async def setup(bot: Bot) -> None:
    """Load the Mathdoku cog."""
    from .mathdoku_parser import create_grids

    try:
        grids = await asyncio.to_thread(create_grids)
    except Exception:
        log.exception("Failed to create Mathdoku grids during setup()")
        grids = []
    await bot.add_cog(Mathdoku(bot, grids))

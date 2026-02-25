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

import re


# These 2 commands make the API not work for some reason if uncommented
# from .mathdoku_parser import create_grids
# grids = create_grids()


CROSS_EMOJI = "\u274e"
log = get_logger(__name__)


class Mathdoku(commands.Cog):
    """Play a game of Mathdoku."""

    def __init__(self, bot: Bot, grids: list):
        self.bot = bot
        self.grids = grids
        self.playing = False
        self.player_id = None

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

        self.playing = True
        while self.playing == True:
            await self.input_number_on_board(ctx)

        await ctx.send("Game of Mathdoku is over!")

    async def input_number_on_board(
        self,
        ctx: commands.Context,
    ) -> None:  # None might need to be changed later
        """Lets the player choose a square and input a number if it is valid."""
        turn_message = await ctx.send(
            "Type the square and what number you want to input. Format it like this: A1 3\n" "Type `end` to end game."
        )
        while True:
            try:
                await self.bot.wait_for("message", check=self.predicate, timeout=60.0)
            except TimeoutError:
                await ctx.send("You took too long. Game over!")
                self.playing = False
                break
            else:
                if not self.playing:
                    await ctx.send("The game has been ended")
                    break
                else:
                    break
        await turn_message.delete()

    def predicate(self, message: discord.Message) -> bool:
        """Predicate checking the message typed for each turn."""
        if self.player_id == message.author.id:
            input_text = message.content.strip()

            if input_text.lower() == "end":
                self.playing = False
                return True
            match = re.fullmatch(r"[A-Ja-j](10|[1-9])\s+[1-9]", input_text)

            # might wanna change to another format
            if not match:
                self.bot.loop.create_task(message.add_reaction(CROSS_EMOJI))
            return bool(match)
        else: 
            return None


async def setup(bot: Bot) -> None:
    """Load the Mathdoku cog."""
    from .mathdoku_parser import create_grids

    try:
        grids = await asyncio.to_thread(create_grids)
    except Exception:
        log.exception("Failed to create Mathdoku grids during setup()")
        grids = []
    await bot.add_cog(Mathdoku(bot, grids))

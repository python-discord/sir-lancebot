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


# These 2 commands make the API not work for some reason if uncommented
# from .mathdoku_parser import create_grids
# grids = create_grids()


class Mathdoku(commands.Cog):
    """Play a game of Mathdoku."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.playing = False

    @commands.group(name="Mathdoku",aliases=("md",), invoke_without_command=True)
    async def mathdoku_group(self, ctx: commands.Context) -> None:
        """Commands for Playing Mathdoku."""
        await ctx.send("The Mathdoku API is working!")
        await self.bot.invoke_help_command(ctx)

    # def predicate(self, message: discord.Message) -> bool:
    #     """Predicate checking the message typed for each turn."""
    #     if message.author == self.turn.user and message.channel == self.turn.user.dm_channel:
    #         if message.content.lower() == "surrender":
    #             self.surrender = True
    #             return True
    #         self.match = re.fullmatch("([A-J]|[a-j]) ?((10)|[1-9])", message.content.strip())
    #         if not self.match:
    #             self.bot.loop.create_task(message.add_reaction(CROSS_EMOJI))
    #         return bool(self.match)
    #     return None

    @mathdoku_group.command(name="start")
    async def start_command(self, ctx: commands.Context, size: int = 5) -> None:
        """Start a game of Mathdoku."""
        await ctx.send("Game of Mathdoku has been started!")

        self.playing = True
        while self.playing == True:
            self.input_number_on_board()

        await ctx.send("Game of Mathdoku is over!")
 
    async def input_number_on_board(self) -> None: #None might need to be changed later
        # """Lets the player choose a square and input a number if it exists."""
        # input_message = await self.send(
        #     "Type the square and what number you want to input. Format it like this: A1 3\n"
        #     "Type `end` to end game."
        # )
    # while True:
    #     try:
    #         await self.bot.wait_for("message", check=self.predicate, timeout=30.0)
    #     except TimeoutError:
    #         await self.send("You took too long. Game over!")
    #         self.gameover = True
    #         break
    #     else:
    #         if self.surrender:
    #             await self.next.user.send(f"{self.turn.user} surrendered. Game over!")
    #             await self.public_channel.send(
    #                 f"Game over! {self.turn.user.mention} surrendered to {self.next.user.mention}!"
    #             )
    #             self.gameover = True
    #             break
    #         square = self.get_square(self.next.grid, self.match.string)
    #         if square.aimed:
    #             await self.turn.user.send("You've already aimed at this square!", delete_after=3.0)
    #         else:
    #             break
    # await turn_message.delete()
    # return square


async def setup(bot: Bot) -> None:
    """Load the Mathdoku cog."""
    await bot.add_cog(Mathdoku(bot))

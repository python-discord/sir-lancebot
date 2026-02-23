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

class Kenken(commands.Cog):
    """Play a game of Kenken."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.group(name="Kenken", invoke_without_command=True)
    async def kenken_group(self, ctx: commands.Context) -> None:
        """Commands for Playing Kenken."""
        await ctx.send("The Kenken API is working!")

async def setup(bot: Bot) -> None:
    """Load the Kenken cog."""
    await bot.add_cog(Kenken(bot))

import logging
import random

from discord.ext import commands
from discord.ext.commands import Context, MessageConverter

from bot.constants import Emojis

log = logging.getLogger(__name__)


class Fun(commands.Cog):
    """A collection of general commands for fun."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, num_rolls: int = 1):
        """Outputs a number of random dice emotes (up to 6)."""
        output = ""
        if num_rolls > 6:
            num_rolls = 6
        elif num_rolls < 1:
            output = ":no_entry: You must roll at least once."
        for _ in range(num_rolls):
            terning = f"terning{random.randint(1, 6)}"
            output += getattr(Emojis, terning, '')
        await ctx.send(output)

    @commands.group(name="randomcase", aliases=("rcase", "randomcaps", "rcaps",), invoke_without_command=True)
    async def randomcase_group(self, ctx: Context, *, text: str) -> None:
        """Commands for returning text in randomcase"""
        await ctx.invoke(self.convert_randomcase, text=text)

    @randomcase_group.command(name="convert")
    async def convert_randomcase(self, ctx: Context, *, text: str) -> None:
        """Randomly converts the casing of a given `text`"""
        text = await Fun.text_to_message(ctx, text)
        converted = (
            char.upper() if round(random.random()) else char.lower() for char in text
        )
        await ctx.send(f">>> {''.join(converted)}")

    @staticmethod
    async def text_to_message(ctx: Context, text: str) -> str:
        """
        Attempts to convert a given `text` to a discord Message, then return the contents.

        Returns `text` if the conversion fails.
        """
        try:
            message = await MessageConverter().convert(ctx, text)
        except commands.BadArgument:
            log.debug(f"Input {text} is not a valid Discord Message")
        else:
            text = message.content
        finally:
            return text


def setup(bot):
    """Fun Cog load."""
    bot.add_cog(Fun(bot))
    log.info("Fun cog loaded")

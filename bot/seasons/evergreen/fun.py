import logging
import random

from discord.ext import commands
from discord.ext.commands import Bot, Cog, Context, MessageConverter

from bot import utils
from bot.constants import Emojis

log = logging.getLogger(__name__)

UWU_WORDS = {
    "fi": "fwi",
    "l": "w",
    "r": "w",
    "th": "d",
    "thing": "fing",
    "tho": "fo",
    "you're": "yuw'we",
    "your": "yur",
    "you": "yuw",
}


class Fun(Cog):
    """A collection of general commands for fun."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.command()
    async def roll(self, ctx: Context, num_rolls: int = 1) -> None:
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

    @commands.command(name="uwu", aliases=("uwuwize", "uwuify",))
    async def uwu_command(self, ctx: Context, *, text: str) -> None:
        """Converts a given `text` into it's uwu equivalent."""
        text = await Fun.get_discord_message(ctx, text)
        converted = utils.replace_many(text, UWU_WORDS, ignore_case=True, match_case=True)
        await ctx.send(f">>> {converted}")

    @commands.command(name="randomcase", aliases=("rcase", "randomcaps", "rcaps",))
    async def randomcase_command(self, ctx: Context, *, text: str) -> None:
        """Randomly converts the casing of a given `text`."""
        text = await Fun.get_discord_message(ctx, text)
        converted = (
            char.upper() if round(random.random()) else char.lower() for char in text
        )
        await ctx.send(f">>> {''.join(converted)}")

    @staticmethod
    async def get_discord_message(ctx: Context, text: str) -> str:
        """
        Attempts to convert a given `text` to a discord Message object, then return the contents.

        Useful if the user enters a link or an id to a valid Discord message, because the contents
        of the message get returned.

        Returns `text` if the conversion fails.
        """
        try:
            message = await MessageConverter().convert(ctx, text)
        except commands.BadArgument:
            log.debug(f"Input '{text:.20}...' is not a valid Discord Message")
        else:
            text = message.content
        finally:
            return text


def setup(bot: commands.Bot) -> None:
    """Fun Cog load."""
    bot.add_cog(Fun(bot))
    log.info("Fun cog loaded")

import random
from typing import Tuple

from discord.ext import commands

from bot.bot import Bot
from bot.constants import Emojis


class CoinSide(commands.Converter):
    """Class used to convert the `side` parameter of coinflip command."""

    HEADS: Tuple[str] = ("h", "head", "heads")
    TAILS: Tuple[str] = ("t", "tail", "tails")

    async def convert(self, ctx: commands.Context, side: str) -> str:
        """Converts the provided `side` into the corresponding string."""
        side = side.lower()
        if side in self.HEADS:
            return "heads"

        if side in self.TAILS:
            return "tails"

        raise commands.BadArgument(f"{side!r} is not a valid coin side.")


class CoinFlip(commands.Cog):
    """Cog for the CoinFlip command."""

    @commands.command(name="coinflip", aliases=("flip", "coin", "cf"))
    async def coinflip_command(self, ctx: commands.Context, side: CoinSide = None) -> None:
        """
        Flips a coin.

        If `side` is provided will state whether you guessed the side correctly.
        """
        flipped_side = random.choice(["heads", "tails"])

        message = f"{ctx.author.mention} flipped **{flipped_side}**. "
        if not side:
            await ctx.send(message)
            return

        if side == flipped_side:
            message += f"You guessed correctly! {Emojis.lemon_hyperpleased}"
        else:
            message += f"You guessed incorrectly. {Emojis.lemon_pensive}"
        await ctx.send(message)


async def setup(bot: Bot) -> None:
    """Loads the coinflip cog."""
    await bot.add_cog(CoinFlip())

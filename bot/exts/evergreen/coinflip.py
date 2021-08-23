import random
from typing import Optional, Tuple

from discord.ext import commands

from bot.bot import Bot


LEMON_HYPERPLEASED = "<:lemon_hyperpleased:754441879822663811>"
LEMON_PENSIVE = "<:lemon_pensive:754441880246419486>"


class CoinSide(commands.Converter):
    """Class used to convert the `side` parameter of coinflip command."""

    HEADS: Tuple[str] = ("h", "head", "heads")
    TAILS: Tuple[str] = ("t", "tail", "tails")

    async def convert(self, ctx: commands.Context, side: str) -> str:
        """Converts the provided `side` into the corresponding string."""
        if side in CoinSide.HEADS:
            return "heads"

        elif side in CoinSide.TAILS:
            return "tails"

        else:
            raise commands.BadArgument(f"{side!r} is not a valid coin side.")


class CoinFlip(commands.Cog):
    """Cog for the CoinFlip command."""

    @commands.command(name="coinflip", aliases=("flip", "coin", "cf"))
    async def coinflip_command(self, ctx: commands.Context, side: Optional[CoinSide]) -> None:
        """
        Flips a coin.

        If `coin_side` is provided will state whether you guessed the side correctly.
        """
        flipped_side = random.choice(["heads", "tails"])

        if not side:
            await ctx.send(f"{ctx.author.mention} Flipped **{flipped_side}**!")
            return

        message = f"{ctx.author.mention} Flipped **{flipped_side}**. "
        if side == flipped_side:
            message += f"You guessed correctly! {LEMON_HYPERPLEASED}"
        else:
            message += f"You guessed incorrectly. {LEMON_PENSIVE}"
        await ctx.send(message)


def setup(bot: Bot) -> None:
    """Loads the coinflip cog."""
    bot.add_cog(CoinFlip())

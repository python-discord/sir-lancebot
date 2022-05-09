import bisect
import hashlib
import json
import logging
import random
from pathlib import Path
from typing import Coroutine, Optional

import discord
from discord import Member
from discord.ext import commands
from discord.ext.commands import BadArgument, Cog, clean_content

from bot.bot import Bot
from bot.constants import Channels, Lovefest, Month, PYTHON_PREFIX
from bot.utils.decorators import in_month

log = logging.getLogger(__name__)

LOVE_DATA = json.loads(Path("bot/resources/holidays/valentines/love_matches.json").read_text("utf8"))
LOVE_DATA = sorted((int(key), value) for key, value in LOVE_DATA.items())


class LoveCalculator(Cog):
    """A cog for calculating the love between two people."""

    @in_month(Month.FEBRUARY)
    @commands.command(aliases=("love_calculator", "love_calc"))
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def love(self, ctx: commands.Context, who: Member, whom: Optional[Member] = None) -> None:
        """
        Tells you how much the two love each other.

        This command requires at least one member as input, if two are given love will be calculated between
        those two users, if only one is given, the second member is assumed to be the invoker.
        Members are converted from:
          - User ID
          - Mention
          - name#discrim
          - name
          - nickname

        Any two arguments will always yield the same result, regardless of the order of arguments:
          Running .love @joe#6000 @chrisjl#2655 will always yield the same result.
          Running .love @chrisjl#2655 @joe#6000 will yield the same result as before.
        """
        if (
            Lovefest.role_id not in [role.id for role in who.roles]
            or (whom is not None and Lovefest.role_id not in [role.id for role in whom.roles])
        ):
            raise BadArgument(
                "This command can only be ran against members with the lovefest role! "
                "This role be can assigned by running "
                f"`{PYTHON_PREFIX}subscribe` in <#{Channels.bot_commands}>."
            )

        if whom is None:
            whom = ctx.author

        def normalize(arg: Member) -> Coroutine:
            # This has to be done manually to be applied to usernames
            return clean_content(escape_markdown=True).convert(ctx, str(arg))

        # Sort to ensure same result for same input, regardless of order
        who, whom = sorted([await normalize(arg) for arg in (who, whom)])

        # Hash inputs to guarantee consistent results (hashing algorithm choice arbitrary)
        #
        # hashlib is used over the builtin hash() to guarantee same result over multiple runtimes
        m = hashlib.sha256(who.encode() + whom.encode())
        # Mod 101 for [0, 100]
        love_percent = sum(m.digest()) % 101

        # We need the -1 due to how bisect returns the point
        # see the documentation for further detail
        # https://docs.python.org/3/library/bisect.html#bisect.bisect
        love_threshold = [threshold for threshold, _ in LOVE_DATA]
        index = bisect.bisect(love_threshold, love_percent) - 1
        # We already have the nearest "fit" love level
        # We only need the dict, so we can ditch the first element
        _, data = LOVE_DATA[index]

        status = random.choice(data["titles"])
        embed = discord.Embed(
            title=status,
            description=f"{who} \N{HEAVY BLACK HEART} {whom} scored {love_percent}%!\n\u200b",
            color=discord.Color.dark_magenta()
        )
        embed.add_field(
            name="A letter from Dr. Love:",
            value=data["text"]
        )
        embed.set_footer(text=f"You can unsubscribe from lovefest by using {PYTHON_PREFIX}subscribe.")

        await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Load the Love calculator Cog."""
    bot.add_cog(LoveCalculator())

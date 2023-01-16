import logging
import random
import re
from typing import NamedTuple

import discord
from discord.ext.commands import Cog

from bot.bot import Bot
from bot.constants import Month
from bot.utils import resolve_current_month
from bot.utils.decorators import in_month

log = logging.getLogger(__name__)


class Trigger(NamedTuple):
    """Representation of regex trigger and corresponding reactions."""

    regex: str
    reaction: list[str]


class Holiday(NamedTuple):
    """Representation of reaction holidays."""

    months: list[Month]
    triggers: dict[str, Trigger]


Valentines = Holiday([Month.FEBRUARY], {
    "heart": Trigger(r"\blove|heart\b", ["\u2764\uFE0F"]),
    }
)
Easter = Holiday([Month.APRIL], {
    "bunny": Trigger(r"\beaster|bunny|rabbit\b", ["\U0001F430", "\U0001F407"]),
    "egg": Trigger(r"\begg\b", ["\U0001F95A"]),
    }
)
EarthDay = Holiday([Month.FEBRUARY], {
    "earth": Trigger(r"\bearth|planet\b", ["\U0001F30E", "\U0001F30D", "\U0001F30F",]),
    }
)
Pride = Holiday([Month.JUNE], {
    "pride": Trigger(r"\bpride\b", ["\U0001F3F3\uFE0F\u200D\U0001F308"]),
    }
)
Halloween = Holiday([Month.OCTOBER], {
    "spooky": Trigger(r"\bspo{2,}[k|p][i|y](er|est)?\b", ["\U0001F47B"]),
    "skeleton": Trigger(r"\bskeleton\b", ["\U0001F480"]),
    "doot": Trigger(r"\bdo{2,}t\b", ["\U0001F480"]),
    "pumpkin": Trigger(r"\bpumpkin\b", ["\U0001F383"]),
    "halloween": Trigger(r"\bhalloween\b", ["\U0001F383"]),
    "jack-o-lantern": Trigger(r"\bjack-o-lantern\b", ["\U0001F383"]),
    "danger": Trigger(r"\bdanger\b", ["\U00002620"]),
    "bat": Trigger(r"\bbat((wo)?m[ae]n|persons?|people|s)?\b", ["\U0001F987"]),
    }
)
Hanukkah = Holiday([Month.NOVEMBER, Month.DECEMBER], {
    "menorah": Trigger(r"\bc?haukkah|menorah\b", ["\U0001F54E"]),
    }
)
Christmas = Holiday([Month.DECEMBER], {
    "christmas tree": Trigger(r"\b(christ|x)mas|tree\b", ["\U0001F384"]),
    "snowflake": Trigger(r"\b(snow ?)?flake(?! ?8)\b", ["\u2744\uFE0F"]),
    "santa": Trigger(r"\bsanta\b", ["\U0001F385"]),
    "snowman": Trigger(r"\bsnow(man|angel)\b", ["\u2603\uFE0F", "\u26C4"]),
    "reindeer": Trigger(r"\breindeer|caribou|buck|stag\b", ["\U0001F98C"]),
    }
)
HOLIDAYS_TO_REACT = [
    Valentines, Easter, EarthDay, Pride, Halloween, Hanukkah, Christmas
]
# Type (or order) doesn't matter here - set is for de-duplication
MONTHS_TO_REACT = set(
    month for holiday in HOLIDAYS_TO_REACT for month in holiday.months
)


class HolidayReact(Cog):
    """A cog that makes the bot react to message triggers."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @in_month(*MONTHS_TO_REACT)
    @Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Triggered when the bot sees a message in a holiday month."""
        # Check message for bot replies and/or command invocations
        # Short circuit if they're found, logging is handled in _short_circuit_check
        if await self._short_circuit_check(message):
            return

        for holiday in HOLIDAYS_TO_REACT:
            await self._check_message(message, holiday)

    async def _check_message(self, message: discord.Message, holiday: Holiday) -> None:
        """
        Checks if message is reactable.

        First checks if month is valid (else return). Then attempts to
        match regex triggers to message. Those that succeed result in
        reactions applied to the message.
        """
        if resolve_current_month() not in holiday.months:
            return

        for name, trigger in holiday.triggers.items():
            trigger_test = re.search(trigger.regex, message.content, flags=re.IGNORECASE)
            if trigger_test:
                if await self._short_circuit_check(message):
                    return
                await message.add_reaction(random.choice(trigger.reaction))
                log.info(f"Added {name!r} reaction to message ID: {message.id}")

    async def _short_circuit_check(self, message: discord.Message) -> bool:
        """
        Short-circuit helper check.

        Return True if:
          * author is a bot
          * prefix is not None
        """
        # Check if message author is a bot
        if message.author.bot:
            log.debug(f"Ignoring reactions on bot message. Message ID: {message.id}")
            return True

        # Check for command invocation
        # Because on_message doesn't give a full Context object, generate one first
        ctx = await self.bot.get_context(message)
        if ctx.prefix:
            log.debug(f"Ignoring reactions on command invocation. Message ID: {message.id}")
            return True

        return False


async def setup(bot: Bot) -> None:
    """Load the Holiday Reaction Cog."""
    await bot.add_cog(HolidayReact(bot))

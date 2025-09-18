import random
import re
from typing import NamedTuple

import discord
from discord.ext.commands import Cog
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import Month
from bot.utils import resolve_current_month
from bot.utils.decorators import in_month

log = get_logger(__name__)


class Trigger(NamedTuple):
    """Representation of regex trigger and corresponding reactions."""

    regex: str
    reaction: list[str]


class Holiday(NamedTuple):
    """Representation of reaction holidays."""

    months: list[Month]
    triggers: dict[str, Trigger]


Valentines = Holiday(
    [Month.FEBRUARY],
    {
        "heart": Trigger(
            r"\b((l|w)(ove|uv)(s|lies?)?|hearts?)\b",
            [
                "\u2764\ufe0f",  # heart
                "\u2665\ufe0f",  # hearts
                "\U0001f49c",    # purple_heart
                "\U0001f49f",    # heart_decoration
                "\U0001f5a4",    # black_heart
                "\U0001f499",    # blue_heart
                "\U0001f90e",    # brown_heart
                "\U0001f49d",    # gift_heart
                "\U0001f49a",    # green_heart
                "\U0001fa76",    # grey_heart
                "\U0001fa75",    # light_blue_heart
                "\U0001f9e1",    # orange_heart
                "\U0001f49b",    # yellow_heart
                "\U0001f49e",    # revolving_hearts
                "\U0001f496",    # sparkling_heart
                "\U0001f90d",    # white_heart
            ],
        )
    }
)
Easter = Holiday([Month.APRIL], {
    "bunny": Trigger(r"\b(easter|bunny|rabbit)\b", ["\U0001F430", "\U0001F407"]),
    "egg": Trigger(r"\begg\b", ["\U0001F95A"]),
    }
)
EarthDay = Holiday([Month.APRIL], {
    "earth": Trigger(r"\b(earth|planet)\b", ["\U0001F30E", "\U0001F30D", "\U0001F30F"]),
    }
)
Pride = Holiday([Month.JUNE], {
    "pride": Trigger(r"\bpride\b", ["\U0001F3F3\uFE0F\u200D\U0001F308"]),
    }
)
Halloween = Holiday([Month.OCTOBER], {
    "bat": Trigger(r"\bbat((wo)?m[ae]n|persons?|people|s)?\b", ["\U0001F987"]),
    "danger": Trigger(r"\bdanger\b", ["\U00002620"]),
    "doot": Trigger(r"\bdo{2,}t\b", ["\U0001F480"]),
    "halloween": Trigger(r"\bhalloween\b", ["\U0001F383"]),
    "jack-o-lantern": Trigger(r"\bjack-o-lantern\b", ["\U0001F383"]),
    "pumpkin": Trigger(r"\bpumpkin\b", ["\U0001F383"]),
    "skeleton": Trigger(r"\bskeleton\b", ["\U0001F480"]),
    "spooky": Trigger(r"\bspo{2,}[k|p][i|y](er|est)?\b", ["\U0001F47B"]),
    }
)
Hanukkah = Holiday([Month.NOVEMBER, Month.DECEMBER], {
    "menorah": Trigger(r"\b(c?hanukkah|menorah)\b", ["\U0001F54E"]),
    }
)
Christmas = Holiday([Month.DECEMBER], {
    "christmas tree": Trigger(r"\b(christ|x)mas\b", ["\U0001F384"]),
    "reindeer": Trigger(r"\b(reindeer|caribou|buck|stag)\b", ["\U0001F98C"]),
    "santa": Trigger(r"\bsanta\b", ["\U0001F385"]),
    "snowflake": Trigger(r"\b(snow ?)?flake(?! ?8)\b", ["\u2744\uFE0F"]),
    "snowman": Trigger(r"\bsnow(man|angel)\b", ["\u2603\uFE0F", "\u26C4"]),
    }
)
HOLIDAYS_TO_REACT = [
    Valentines, Easter, EarthDay, Pride, Halloween, Hanukkah, Christmas
]
# Type (or order) doesn't matter here - set is for de-duplication
MONTHS_TO_REACT = {
    month for holiday in HOLIDAYS_TO_REACT for month in holiday.months
}


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
        Check if message is reactable.

        React to message if:
          * month is valid
          * message contains reaction regex triggers
        """
        if resolve_current_month() not in holiday.months:
            return

        for name, trigger in holiday.triggers.items():
            trigger_test = re.search(trigger.regex, message.content, flags=re.IGNORECASE)
            if trigger_test:
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

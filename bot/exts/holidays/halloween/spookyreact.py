import logging
import re

import discord
from discord.ext.commands import Cog

from bot.bot import Bot
from bot.constants import Month
from bot.utils.decorators import in_month

log = logging.getLogger(__name__)

SPOOKY_TRIGGERS = {
    "spooky": (r"\bspo{2,}ky\b", "\U0001F47B"),
    "skeleton": (r"\bskeleton\b", "\U0001F480"),
    "doot": (r"\bdo{2,}t\b", "\U0001F480"),
    "pumpkin": (r"\bpumpkin\b", "\U0001F383"),
    "halloween": (r"\bhalloween\b", "\U0001F383"),
    "jack-o-lantern": (r"\bjack-o-lantern\b", "\U0001F383"),
    "danger": (r"\bdanger\b", "\U00002620")
}


class SpookyReact(Cog):
    """A cog that makes the bot react to message triggers."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @in_month(Month.OCTOBER)
    @Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Triggered when the bot sees a message in October."""
        for name, trigger in SPOOKY_TRIGGERS.items():
            trigger_test = re.search(trigger[0], message.content.lower())
            if trigger_test:
                # Check message for bot replies and/or command invocations
                # Short circuit if they're found, logging is handled in _short_circuit_check
                if await self._short_circuit_check(message):
                    return
                else:
                    await message.add_reaction(trigger[1])
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
    """Load the Spooky Reaction Cog."""
    await bot.add_cog(SpookyReact(bot))

import logging
import re

import discord

log = logging.getLogger(__name__)

SPOOKY_TRIGGERS = {
    'spooky': (r"\bspo{2,}ky\b", "\U0001F47B"),
    'skeleton': (r"\bskeleton\b", "\U0001F480"),
    'doot': (r"\bdo{2,}t\b", "\U0001F480"),
    'pumpkin': (r"\bpumpkin\b", "\U0001F383"),
    'halloween': (r"\bhalloween\b", "\U0001F383"),
    'jack-o-lantern': (r"\bjack-o-lantern\b", "\U0001F383"),
    'danger': (r"\bdanger\b", "\U00002620")
}


class SpookyReact:

    """
    A cog that makes the bot react to message triggers.
    """

    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, ctx: discord.Message):
        """
        A command to send the seasonalbot github project

        Lines that begin with the bot's command prefix are ignored

        Seasonalbot's own messages are ignored
        """
        for trigger in SPOOKY_TRIGGERS.keys():
            trigger_test = re.search(SPOOKY_TRIGGERS[trigger][0], ctx.content.lower())
            if trigger_test:
                # Check message for bot replies and/or command invocations
                # Short circuit if they're found, logging is handled in _short_circuit_check
                if await self._short_circuit_check(ctx):
                    return
                else:
                    await ctx.add_reaction(SPOOKY_TRIGGERS[trigger][1])
                    logging.info(f"Added '{trigger}' reaction to message ID: {ctx.id}")

    async def _short_circuit_check(self, ctx: discord.Message) -> bool:
        """
        Short-circuit helper check.

        Return True if:
          * author is the bot
          * prefix is not None
        """
        # Check for self reaction
        if ctx.author == self.bot.user:
            logging.debug(f"Ignoring reactions on self message. Message ID: {ctx.id}")
            return True

        # Check for command invocation
        # Because on_message doesn't give a full Context object, generate one first
        tmp_ctx = await self.bot.get_context(ctx)
        if tmp_ctx.prefix:
            logging.debug(f"Ignoring reactions on command invocation. Message ID: {ctx.id}")
            return True

        return False


def setup(bot):
    bot.add_cog(SpookyReact(bot))
    log.debug("SpookyReact cog loaded")

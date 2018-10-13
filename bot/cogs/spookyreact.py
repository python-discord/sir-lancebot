import logging
import re

import discord

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
        A command to send the hacktoberbot github project

        Lines that begin with the bot's command prefix are ignored
        """
        await ctx.channel.send("spooky")
        # Short-circuit if bot tries to react to itself
        if ctx.author == self.bot.user:
            logging.info(f"Bot self-react short-circuited. Message ID: {ctx.id}")
            return

        # Check for & ignore messages with bot commands, since we're in on_message
        # we don't have a Context object, so we need to generate a temporary one
        tmp_ctx = await self.bot.get_context(ctx)
        if not tmp_ctx.prefix:
            for trigger in SPOOKY_TRIGGERS.keys():
                trigger_test = re.search(SPOOKY_TRIGGERS[trigger][0], ctx.content.lower())
                if trigger_test:
                    await ctx.add_reaction(SPOOKY_TRIGGERS[trigger][1])
                    logging.info(f"Added '{trigger}' reaction to message ID: {ctx.id}")
        else:
            logging.info(f"Ignoring reaction on command invocation. Message ID: {ctx.id}")


def setup(bot):
    bot.add_cog(SpookyReact(bot))

import logging

import arrow
from dateutil.relativedelta import relativedelta
from discord.ext import commands

from bot import start_time
from bot.bot import Bot

log = logging.getLogger(__name__)


class Uptime(commands.Cog):
    """A cog for posting the bot's uptime."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="uptime")
    async def uptime(self, ctx: commands.Context) -> None:
        """Responds with the uptime of the bot."""
        difference = relativedelta(start_time - arrow.utcnow())
        uptime_string = start_time.shift(
            seconds=-difference.seconds,
            minutes=-difference.minutes,
            hours=-difference.hours,
            days=-difference.days
        ).humanize()
        await ctx.send(f"I started up {uptime_string}.")


def setup(bot: Bot) -> None:
    """Load the Uptime cog."""
    bot.add_cog(Uptime(bot))

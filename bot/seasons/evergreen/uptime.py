import logging

import arrow
from dateutil.relativedelta import relativedelta
from discord.ext import commands

from bot import start_time

log = logging.getLogger(__name__)


class Uptime(commands.Cog):
    """A cog for posting the bot's uptime."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="uptime")
    async def uptime(self, ctx):
        """Responds with the uptime of the bot."""
        difference = relativedelta(start_time - arrow.utcnow())
        uptime_string = start_time.shift(
            seconds=-difference.seconds,
            minutes=-difference.minutes,
            hours=-difference.hours,
            days=-difference.days
        ).humanize()
        await ctx.send(f"I started up {uptime_string}.")


def setup(bot):
    """Uptime Cog load."""
    bot.add_cog(Uptime(bot))
    log.info("Uptime cog loaded")

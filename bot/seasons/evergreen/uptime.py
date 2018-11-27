import logging

import arrow
from dateutil.relativedelta import relativedelta
from discord.ext import commands

from bot import start_time

log = logging.getLogger(__name__)


class Uptime:
    """
    A cog for posting the bots uptime.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="uptime")
    async def uptime(self, ctx):
        """
        Returns the uptime of the bot.
        """
        difference = relativedelta(start_time - arrow.utcnow())
        uptime_string = start_time.shift(
            seconds=-difference.seconds,
            minutes=-difference.minutes,
            hours=-difference.hours,
            days=-difference.days
        ).humanize()
        await ctx.send(f"I started up {uptime_string}.")


# Required in order to load the cog, use the class name in the add_cog function.
def setup(bot):
    bot.add_cog(Uptime(bot))
    log.debug("Uptime cog loaded")

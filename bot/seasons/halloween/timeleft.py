import logging
from datetime import datetime

from discord.ext import commands

log = logging.getLogger(__name__)


class TimeLeft:
    """
    A Cog that tells you how long left until Hacktober is over!
    """

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def in_october():
        """
        Return True if the current month is October.
        """

        return datetime.utcnow().month == 10

    @staticmethod
    def load_date():
        """
        Return of a tuple of the current time and the end and start times of the following October.
        """

        now = datetime.utcnow()
        year = now.year
        if now.month > 10:
            year += 1
        end = datetime(year, 10, 31, 11, 59, 59)
        start = datetime(year, 10, 1)
        return now, end, start

    @commands.command()
    async def timeleft(self, ctx):
        """
        Calculates the time left until the end of Hacktober.

        Whilst in October, displays the days, hours and minutes left.
        Only displays the days left until the beginning and end whilst in a different month
        """

        now, end, start = self.load_date()
        diff = end - now
        days, seconds = diff.days, diff.seconds
        if self.in_october():
            minutes = seconds // 60
            hours, minutes = divmod(minutes, 60)
            await ctx.send(f"There is currently only {days} days, {hours} hours and {minutes}"
                           "minutes left until the end of Hacktober.")
        else:
            start_diff = start - now
            start_days = start_diff.days
            await ctx.send(
                f"It is not currently Hacktober. However, the next one will start in {start_days} days "
                f"and will finish in {days} days."
            )


def setup(bot):
    bot.add_cog(TimeLeft(bot))
    log.info("TimeLeft cog loaded")

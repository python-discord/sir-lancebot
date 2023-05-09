import logging
from datetime import UTC, datetime

from discord.ext import commands

from bot.bot import Bot

log = logging.getLogger(__name__)


class TimeLeft(commands.Cog):
    """A Cog that tells users how long left until Hacktober is over!"""

    def in_hacktober(self) -> bool:
        """Return True if the current time is within Hacktoberfest."""
        _, end, start = self.load_date()

        now = datetime.now(tz=UTC)

        return start <= now <= end

    @staticmethod
    def load_date() -> tuple[datetime, datetime, datetime]:
        """Return of a tuple of the current time and the end and start times of the next Hacktober."""
        now = datetime.now(tz=UTC)
        year = now.year
        if now.month > 10:
            year += 1
        end = datetime(year, 11, 1, 12, tzinfo=UTC)  # November 1st 12:00 (UTC-12:00)
        start = datetime(year, 9, 30, 10, tzinfo=UTC)  # September 30th 10:00 (UTC+14:00)
        return now, end, start

    @commands.command()
    async def timeleft(self, ctx: commands.Context) -> None:
        """
        Calculates the time left until the end of Hacktober.

        Whilst in October, displays the days, hours and minutes left.
        Only displays the days left until the beginning and end whilst in a different month.

        This factors in that Hacktoberfest starts when it is October anywhere in the world
        and ends with the same rules. It treats the start as UTC+14:00 and the end as
        UTC-12.
        """
        now, end, start = self.load_date()
        diff = end - now
        days, seconds = diff.days, diff.seconds
        if self.in_hacktober():
            minutes = seconds // 60
            hours, minutes = divmod(minutes, 60)

            await ctx.send(
                f"There are {days} days, {hours} hours and {minutes}"
                f" minutes left until the end of Hacktober."
            )
        else:
            start_diff = start - now
            start_days = start_diff.days
            await ctx.send(
                f"It is not currently Hacktober. However, the next one will start in {start_days} days "
                f"and will finish in {days} days."
            )


async def setup(bot: Bot) -> None:
    """Load the Time Left Cog."""
    await bot.add_cog(TimeLeft())

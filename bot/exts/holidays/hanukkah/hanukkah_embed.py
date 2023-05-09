import logging
from datetime import UTC, date, datetime

from discord import Embed
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, Month
from bot.utils.decorators import in_month

log = logging.getLogger(__name__)

HEBCAL_URL = (
    "https://www.hebcal.com/hebcal/?v=1&cfg=json&maj=on&min=on&mod=on&nx=on&"
    "year=now&month=x&ss=on&mf=on&c=on&geo=geoname&geonameid=3448439&m=50&s=on"
)


class HanukkahEmbed(commands.Cog):
    """A cog that returns information about Hanukkah festival."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.hanukkah_dates: list[date] = []

    def _parse_time_to_datetime(self, date: list[str]) -> datetime:
        """Format the times provided by the api to datetime forms."""
        try:
            return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            # there is a possibility of an event not having a time, just a day
            # to catch this, we try again without time information
            return datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=UTC)

    async def fetch_hanukkah_dates(self) -> list[date]:
        """Gets the dates for hanukkah festival."""
        # clear the datetime objects to prevent a memory link
        self.hanukkah_dates = []
        async with self.bot.http_session.get(HEBCAL_URL) as response:
            json_data = await response.json()
        festivals = json_data["items"]
        for festival in festivals:
            if festival["title"].startswith("Chanukah"):
                date = festival["date"]
                self.hanukkah_dates.append(self._parse_time_to_datetime(date).date())
        return self.hanukkah_dates

    @in_month(Month.NOVEMBER, Month.DECEMBER)
    @commands.command(name="hanukkah", aliases=("chanukah",))
    async def hanukkah_festival(self, ctx: commands.Context) -> None:
        """Tells you about the Hanukkah Festivaltime of festival, festival day, etc)."""
        hanukkah_dates = await self.fetch_hanukkah_dates()
        start_day = hanukkah_dates[0]
        end_day = hanukkah_dates[-1]
        today = datetime.now(tz=UTC).date()
        embed = Embed(title="Hanukkah", colour=Colours.blue)
        if start_day <= today <= end_day:
            if start_day == today:
                now = datetime.now(tz=UTC)
                hours = now.hour + 4  # using only hours
                hanukkah_start_hour = 18
                if hours < hanukkah_start_hour:
                    embed.description = (
                        "Hanukkah hasnt started yet, "
                        f"it will start in about {hanukkah_start_hour - hours} hour/s."
                    )
                    await ctx.send(embed=embed)
                    return

                if hours > hanukkah_start_hour:
                    embed.description = (
                        "It is the starting day of Hanukkah! "
                        f"Its been {hours - hanukkah_start_hour} hours hanukkah started!"
                    )
                    await ctx.send(embed=embed)
                    return
            festival_day = hanukkah_dates.index(today)
            number_suffixes = ["st", "nd", "rd", "th"]
            suffix = number_suffixes[festival_day - 1 if festival_day <= 3 else 3]
            message = ":menorah:" * festival_day
            embed.description = (
                f"It is the {festival_day}{suffix} day of Hanukkah!\n{message}"
            )
        elif today < start_day:
            format_start = start_day.strftime("%d of %B")
            embed.description = (
                "Hanukkah has not started yet. "
                f"Hanukkah will start at sundown on {format_start}."
            )
        else:
            format_end = end_day.strftime("%d of %B")
            embed.description = (
                "Looks like you missed Hanukkah! "
                f"Hanukkah ended on {format_end}."
            )

        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the Hanukkah Embed Cog."""
    await bot.add_cog(HanukkahEmbed(bot))

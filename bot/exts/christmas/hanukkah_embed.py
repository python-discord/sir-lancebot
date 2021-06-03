import datetime
import logging
from typing import List

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
        self.hanukkah_days = []
        self.hanukkah_months = []
        self.hanukkah_years = []

    async def get_hanukkah_dates(self) -> List[str]:
        """Gets the dates for hanukkah festival."""
        hanukkah_dates = []
        async with self.bot.http_session.get(HEBCAL_URL) as response:
            json_data = await response.json()
        festivals = json_data["items"]
        for festival in festivals:
            if festival["title"].startswith("Chanukah"):
                date = festival["date"]
                hanukkah_dates.append(date)
        return hanukkah_dates

    @in_month(Month.DECEMBER)
    @commands.command(name="hanukkah", aliases=("chanukah",))
    async def hanukkah_festival(self, ctx: commands.Context) -> None:
        """Tells you about the Hanukkah Festivaltime of festival, festival day, etc)."""
        hanukkah_dates = await self.get_hanukkah_dates()
        self.hanukkah_dates_split(hanukkah_dates)
        hanukkah_start_day = int(self.hanukkah_days[0])
        hanukkah_start_month = int(self.hanukkah_months[0])
        hanukkah_start_year = int(self.hanukkah_years[0])
        hanukkah_end_day = int(self.hanukkah_days[8])
        hanukkah_end_month = int(self.hanukkah_months[8])
        hanukkah_end_year = int(self.hanukkah_years[8])

        hanukkah_start = datetime.date(hanukkah_start_year, hanukkah_start_month, hanukkah_start_day)
        hanukkah_end = datetime.date(hanukkah_end_year, hanukkah_end_month, hanukkah_end_day)
        today = datetime.date.today()
        # today = datetime.date(2019, 12, 24) (for testing)
        day = str(today.day)
        month = str(today.month)
        year = str(today.year)
        embed = Embed(title="Hanukkah", colour=Colours.blue)
        if day in self.hanukkah_days and month in self.hanukkah_months and year in self.hanukkah_years:
            if int(day) == hanukkah_start_day:
                now = datetime.datetime.utcnow()
                hours = now.hour + 4  # using only hours
                hanukkah_start_hour = 18
                if hours < hanukkah_start_hour:
                    embed.description = (
                        "Hanukkah hasnt started yet, "
                        f"it will start in about {hanukkah_start_hour - hours} hour/s."
                    )
                    await ctx.send(embed=embed)
                    return
                elif hours > hanukkah_start_hour:
                    embed.description = (
                        "It is the starting day of Hanukkah! "
                        f"Its been {hours - hanukkah_start_hour} hours hanukkah started!"
                    )
                    await ctx.send(embed=embed)
                    return
            festival_day = self.hanukkah_days.index(day)
            number_suffixes = ["st", "nd", "rd", "th"]
            suffix = number_suffixes[festival_day - 1 if festival_day <= 3 else 3]
            message = ":menorah:" * festival_day
            embed.description = f"It is the {festival_day}{suffix} day of Hanukkah!\n{message}"
            await ctx.send(embed=embed)
        else:
            if today < hanukkah_start:
                festival_starting_month = hanukkah_start.strftime("%B")
                embed.description = (
                    f"Hanukkah has not started yet. "
                    f"Hanukkah will start at sundown on {hanukkah_start_day}th "
                    f"of {festival_starting_month}."
                )
            else:
                festival_end_month = hanukkah_end.strftime("%B")
                embed.description = (
                    f"Looks like you missed Hanukkah!"
                    f"Hanukkah ended on {hanukkah_end_day}th of {festival_end_month}."
                )

            await ctx.send(embed=embed)

    def hanukkah_dates_split(self, hanukkah_dates: List[str]) -> None:
        """We are splitting the dates for hanukkah into days, months and years."""
        for date in hanukkah_dates:
            self.hanukkah_days.append(date[8:10])
            self.hanukkah_months.append(date[5:7])
            self.hanukkah_years.append(date[0:4])


def setup(bot: Bot) -> None:
    """Load the Hanukkah Embed Cog."""
    bot.add_cog(HanukkahEmbed(bot))

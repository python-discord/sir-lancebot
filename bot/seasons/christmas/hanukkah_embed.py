import datetime
import logging

import requests
from discord import Embed
from discord.ext import commands


log = logging.getLogger(__name__)

HANUKKAH_DAYS = []
HANUKKAH_MONTHS = []
HANUKKAH_YEARS = []


class HanukkahEmbed(commands.Cog):
    """
    A cog that returns information about Hanukkah festival.
    """
    def __init__(self, bot):
        self.bot = bot
        self.url = """https://www.hebcal.com/hebcal/?v=1&cfg=json&maj=on&min=on&mod=on&nx=on&year=now&month=x&ss=on&
                      mf=on&c=on&geo=geoname&geonameid=3448439&m=50&s=on"""
        self.hanukkah_dates = self.get_hanukkah_dates()

    def get_hanukkah_dates(self):
        """
        Gets the dates for hanukkah festival.
        """
        hanukkah_dates = []
        r = requests.get(self.url)
        json_data = r.json()
        festivals = json_data['items']
        for festival in festivals:
            if festival['title'].startswith('Chanukah'):
                date = festival['date']
                hanukkah_dates.append(date)
        return hanukkah_dates

    @commands.command(name='hanukkah', aliases=['chanukah'])
    async def hanukkah_festival(self, ctx):
        """
        Tells you about the Hanukkah Festival
        (time of festival, festival day, etc)
        """
        self.hanukkah_dates_split()

        hanukkah_start_day = int(HANUKKAH_DAYS[0])
        hanukkah_start_month = int(HANUKKAH_MONTHS[0])
        hanukkah_start_year = int(HANUKKAH_YEARS[0])
        hanukkah_end_day = int(HANUKKAH_DAYS[8])
        hanukkah_end_month = int(HANUKKAH_MONTHS[8])
        hanukkah_end_year = int(HANUKKAH_YEARS[8])

        hanukkah_start = datetime.date(hanukkah_start_year, hanukkah_start_month, hanukkah_start_day)
        hanukkah_end = datetime.date(hanukkah_end_year, hanukkah_end_month, hanukkah_end_day)
        # today = datetime.date.today()
        today = datetime.date(2019, 12, 24)
        day = str(today.day)
        month = str(today.month)
        year = str(today.year)
        embed = Embed()
        embed.title = 'Hanukkah Embed'
        embed.colour = 0x68c290
        if day in HANUKKAH_DAYS and month in HANUKKAH_MONTHS and year in HANUKKAH_YEARS:
            if int(day) == hanukkah_start_day:
                now = datetime.datetime.utcnow()
                now = str(now)
                hours = int(now[11:13]) + 4  # using only hours
                hanukkah_start_hour = 18
                if hours < hanukkah_start_hour:
                    embed.description = (f"Hanukkah hasnt started yet, "
                                         f"it will start in about {hanukkah_start_hour-hours} hour/s.")
                    return await ctx.send(embed=embed)
                elif hours > hanukkah_start_hour:
                    embed.description = (f'It is the starting day of Hanukkah ! '
                                         f'Its been {hours-hanukkah_start_hour} hours hanukkah started !')
                    return await ctx.send(embed=embed)
            festival_day = HANUKKAH_DAYS.index(day)
            number_suffixes = ['st', 'nd', 'rd', 'th']
            suffix = ''
            if int(festival_day) == 1:
                suffix = number_suffixes[0]
            if int(festival_day) == 2:
                suffix = number_suffixes[1]
            if int(festival_day) == 3:
                suffix = number_suffixes[2]
            if int(festival_day) > 3:
                suffix = number_suffixes[3]
            message = ''
            for i in range(1, festival_day + 1):
                message += ':menorah:'
            embed.description = f'It is the {festival_day}{suffix} day of Hanukkah ! \n {message}'
            await ctx.send(embed=embed)
        else:
            if today < hanukkah_start:
                festival_starting_month = hanukkah_start.strftime('%B')
                embed.description = (f"Hanukkah has not started yet. "
                                     f"Hanukkah will start at sundown on {hanukkah_start_day}th "
                                     f"of {festival_starting_month}.")
            else:
                festival_end_month = hanukkah_end.strftime('%B')
                embed.description = (f"Looks like you missed Hanukkah !"
                                     f"Hanukkah ended on {hanukkah_end_day}th of {festival_end_month}.")

            await ctx.send(embed=embed)

    def hanukkah_dates_split(self):
        """
        We are splitting the dates for hanukkah into days, months and years.
        """
        for date in self.hanukkah_dates:
            HANUKKAH_DAYS.append(date[8:10])
            HANUKKAH_MONTHS.append(date[5:7])
            HANUKKAH_YEARS.append(date[0:4])


def setup(bot):
    bot.add_cog(HanukkahEmbed(bot))
    log.info("AdventOfCode cog loaded")

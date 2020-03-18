import datetime
import json
import logging
from pathlib import Path
from typing import List, Tuple

import discord
import requests
from discord.ext.commands import Bot, Cog, Context, command

from bot.pagination import ImagePaginator


logger = logging.getLogger(__name__)
# RESTful API to get countries info
url = "https://restcountries.eu/rest/v2/alpha/"
# white flag image to show during error
white_flag = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/\
White_flag_waving.svg/158px-White_flag_waving.svg.png"
# url to get images of flags
flag_url = "https://www.countryflags.io/"


class NationDay(Cog):
    """NationDay Cog that contains nationday command."""
    
    def __init__(self, bot: Bot):
        self.bot = Bot

    with open(Path("bot/resources/evergreen/nationday/countries_by_day.json"), "r") as file:
        by_day = json.load(file)

    with open(Path("bot/resources/evergreen/nationday/iso_codes.json"), "r") as file:
        iso_codes = json.load(file)

    async def get_key(self, val: str) -> str:
        """Get date for particular country, if present."""
        for key, value in self.by_day.items():
            if val in value:
                return key
        return None

    async def get_specific_country(self, country: str) -> Tuple[List[Tuple[str, str]], str]:
        """
        Get Indepedence Day of given country.
        
        Return Indepedence Day and page of information on country.
        """
        # Get Indepedence Day of specified country
        date = await self.get_key(country)
        if date:
            page, img = await self.get_country_info(country)
            return [(page, img)], date
        return [(None, None)], None

    async def country_today(self) -> List[Tuple[str, str]]:
        """
        Get current day [Month & Day].
        
        Return pages of info and flags of countries.
        """
        # Get current date [Month and day]
        date = datetime.datetime.today()
        month = date.strftime("%B")
        day = date.day
        today_date = f'{month} {day}'
        try:
            # Get list of countries
            countries = self.by_day[today_date]
            countries = list(countries.split(','))
        except Exception as ke:
            err_msg = f"No country has an independence day today. {ke}"
            logger.warning(err_msg)
            return [(err_msg, white_flag)]
        # Create pages
        pages = []
        for country in countries:
            page, img = await self.get_country_info(country)
            pages.append((page, img))
        return pages

    async def get_country_info(self, country: str) -> Tuple[str, str]:
        """
        Create country information page using RESTCountries API.
        
        Return page and flag image.
        """
        try:
            iso_code = self.iso_codes[country]
            result = requests.get(url+iso_code)
            info = result.json()

            country_info = ""
            country_info += f"Region: {info['region']}\n\n"
            country_info += f"Capital: {info['capital']}\n\n"
            country_info += f"Population: {info['population']}\n\n"
            country_info += f"Currency: {info['currencies'][0]['name']} ({info['currencies'][0]['symbol']})\n"
            flag = flag_url+iso_code+"/flat/64.png"

        except Exception as e:
            msg = f"Error! {e}"
            logger.warning(e)
            return msg, white_flag

        return country_info, flag

    @command(name='nationday')
    async def nationday(self, ctx: Context, param: str = "") -> None:
        """
        \U0001F30F NationDay Help.
        
        Enter a country name to get independence day of that country along with some basic information on the country.
        Enter "today" to get all countries whose independence day is the current day, along with information.
        Usage:
        -> .nationday today
        -> .nationday [country]
        Examples:
        -> .nationday india
        -> .nationday colombia
        -> .nationday today
        """
        param = param.capitalize()

        if param == 'Today':
            pages = await self.country_today()
            embed = discord.Embed(
                title='Countries that have their independence days today')\
                    .set_footer(text='Powered by the RESTCountries API.')
            await ImagePaginator.paginate(pages, ctx, embed)

        # Check if country is present
        elif param in self.iso_codes.keys():
            page, date = await self.get_specific_country(param)
            if page[0][0] is not None:
                embed = discord.Embed(
                    title=f'{param} -> {date}')\
                    .set_footer(text='Powered by the RESTCountries API.')
                await ImagePaginator.paginate(page, ctx, embed)

        else:
            await ctx.channel.send("Country entered may not be available OR invalid option used.\
            \nCheck the help section below.")
            await ctx.send_help('nationday')


def setup(bot: Bot) -> None:
    """Load NationDay Cog."""
    bot.add_cog(NationDay(bot))

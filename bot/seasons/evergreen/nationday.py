import json
import logging
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

import discord
from aiohttp import ClientSession
from discord.ext.commands import Bot, Cog, Context, command

from bot.pagination import ImagePaginator


logger = logging.getLogger(__name__)
# RESTful API to get countries info
URL = "https://restcountries.eu/rest/v2/alpha/"
# white flag image to show during error
WHITE_FLAG = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/"
    "White_flag_waving.svg/158px-White_flag_waving.svg.png"
)


class NationDay(Cog):
    """NationDay Cog that to help users get info on countries powered by the RESTCountries API."""

    def __init__(self, bot: Bot):
        self.bot = Bot
        self.http_session: ClientSession = ClientSession()
        with open(Path("bot/resources/evergreen/nationday/countries_by_day.json"), "r") as file:
            self.by_day = json.load(file)

        with open(Path("bot/resources/evergreen/nationday/iso_codes.json"), "r") as file:
            self.iso_codes = json.load(file)

    async def get_date(self, val: str) -> Optional[str]:
        """Get date for particular country, if present."""
        for day, countries in self.by_day.items():
            if val in countries:
                return day
        return None

    async def get_specific_country(self, country: str) -> Tuple[Tuple[str, str], str]:
        """
        Get Indepedence Day of given country.

        Return Indepedence Day and page of information on country.
        """
        # Get date of specified country from dict
        date = await self.get_date(country)
        if date:
            page, img = await self.get_country_info(country)
            return (page, img), date
        return (None, None), None

    async def country_today(self) -> List[Tuple[str, str]]:
        """
        Get current day [Month & Day].

        Return pages of info and flags of countries.
        """
        # Get current date [Month and day]
        today = date.today()
        month = today.strftime("%B")
        day = today.day
        today_date = f'{month} {day}'
        today_date = today_date.lower()
        try:
            # Get list of countries
            countries = self.by_day[today_date]
        except KeyError as ke:
            err_msg = f"**No countries have their independence day today.** {ke}"
            logger.warning(err_msg)
            return [(err_msg, WHITE_FLAG)]
        # Create pages
        countries = list(countries.split(','))
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
        # url to get images of flags
        flag_url = "https://www.countryflags.io/{country_code}/flat/64.png"

        iso_code = self.iso_codes.get(country)
        if iso_code is None:
            not_available_msg = f"This country is not currently available."
            logger.warning(not_available_msg)
            return not_available_msg, WHITE_FLAG

        async with self.http_session.get(URL+iso_code) as resp:
            info = await resp.json()

        # check if 404 error
        if info.get('status') == 404:
            not_found_msg = f"Could not find information on this country."
            logger.warning(not_found_msg)
            return not_found_msg, WHITE_FLAG

        country_info = ""
        country_info += f"**Name**: {info['name']}\n"
        country_info += f"**Region**: {info['region']}\n"
        country_info += f"**Capital**: {info['capital']}\n"
        country_info += f"**Population**: {info['population']:,}\n"
        country_info += f"**Currency**: {info['currencies'][0]['name']} ({info['currencies'][0]['symbol']})\n"
        flag = flag_url.format(country_code=iso_code)

        return country_info, flag

    @command(name='nationday')
    async def nationday(self, ctx: Context, *, arg: str) -> None:
        """
        \U0001F30F NationDay Help.

        Enter a country name to get independence day of that country along with some basic information on the country.
        Enter "today" to get all countries whose independence day is the current day, along with information.
        Usage:
        -> .nationday today
        -> .nationday [country] (use "" for countries with space in the name)
        Examples:
        -> .nationday today
        -> .nationday india
        -> .nationday United Arab Emirates
        -> .nationday Ivory Coast
        """
        arg = arg.lower()

        if arg == 'today':
            pages = await self.country_today()
            embed = discord.Embed(
                title='Countries that have their independence days today'
            ).set_footer(text='Powered by the RESTCountries API.')
            await ImagePaginator.paginate(pages, ctx, embed)

        # Check if country is present
        elif arg in self.iso_codes.keys():
            page, date = await self.get_specific_country(arg)
            embed = discord.Embed(
                title=f'{arg.title()} -> {date.capitalize()}',
                description=page[0]
            ).set_footer(text='Powered by the RESTCountries API.')
            embed.set_image(url=page[1])
            await ctx.channel.send(embed=embed)

        else:
            await ctx.channel.send(
                (
                    "Give appropriate country name Eg. 'United States of America'\n"
                    "**Country entered may not be available** OR an invalid option was used.\n"
                    "Check out the help section below."
                )
            )
            await ctx.send_help('nationday')


def setup(bot: Bot) -> None:
    """Load NationDay Cog."""
    bot.add_cog(NationDay(bot))
    logger.debug("NationDay cog loaded.")

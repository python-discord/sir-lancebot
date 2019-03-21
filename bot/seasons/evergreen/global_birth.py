import json
import logging
from pathlib import Path
from datetime import datetime

# import discord
from discord.ext import commands


log = logging.getLogger(__name__)

with open(Path("bot", "resources", "evergreen", "global_birth.json"), "r") as indep_file:
    indep_info = json.load(indep_file)


class CountriesBirth:
    """
    Compilation of countries independence days, as well as some information about them
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def inform(self, ctx, country_name: str = ""):
        """
        @returns output the name and info on the country(ies) who's birthday is today.
        @returns output the independence information about the country provided
        """
        dates = indep_info["dates"]
        countries = indep_info["countries"]

        output = " The country is who knows"
        if country_name:
            output = f" The country is who knows {country_name}, {len(countries)}"
            if str(country_name) in countries:
                name = countries[country_name][0]["name"]
                # info = countries[country_name][0]["info"]
                output = f" The country is {name}"
        else:
            today = datetime.now()
            month = today.strftime("%B")
            day = str(today.strftime("%d"))

            if day in dates[month]:
                output = []
                for item in dates[month][day]:
                    output.append(item)

        await ctx.send(output)


def setup(bot):
    bot.add_cog(CountriesBirth(bot))

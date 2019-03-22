import json
import logging
from pathlib import Path
from datetime import datetime
from discord.ext import commands


log = logging.getLogger(__name__)


class CountriesBirth:
    """
    Compilation of countries independence days, as well as some information about them
    """

    def __init__(self, bot):
        self.bot = bot
        self.indep_info = self.load_data()

    def load_data(self):
        """
        Loading the json data to be used for the rest of the class
        :return: loaded json data as dictionary
        """
        indep_file = open(Path("bot", "resources", "evergreen", "global_birth.json"), "r")
        return json.load(indep_file)

    async def get_info(self, ctx, country_name: str):
        """
        Processes the country name against the `countries` dictionary in
        :param ctx: takes in ctx to send data to discord channel
        :param country_name: takes in the name of a country to get it's info
        """
        countries = self.indep_info["countries"]
        for info in countries[country_name]:
            # needs to be changed into embed
            counter = []
            counter.append(info["name"])
            counter.append(info["independence"])
            counter.append(info["description"])
            counter.append(info["holiday"])
            # print(counter)
            await ctx.send(counter)

    @commands.command()
    async def inform(self, ctx, country_name: str = None):
        """
        @returns output the name and info on the country(ies) who's birthday is today.
        @returns output the independence information about the country provided
        """
        dates = self.indep_info["dates"]

        if country_name:
            await self.get_info(ctx, country_name)
        else:
            today = datetime.now()
            month = today.strftime("%B")
            day = str(today.strftime("%d"))

            if day in dates[month]:
                for country_name in dates[month][day]:
                    await self.get_info(ctx, country_name)
            else:
                output = "Today is one of the lovely days where no country saw their independence, or at least," \
                         "it is not yet documented"
                await ctx.send(output)


def setup(bot):
    bot.add_cog(CountriesBirth(bot))

import json
import logging
from pathlib import Path
from datetime import datetime

import discord
from discord.ext import commands

from bot.constants import Colours


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

    async def produce_info(self, ctx, country_name: str):
        """
        Processes the country name against the `countries` dictionary in
        :param ctx: takes in ctx to send data to discord channel
        :param country_name: takes in the name of a country to get it's info
        """
        countries = self.indep_info["countries"]
        for info in countries[country_name]:
            # TODO complete and test embed
            embed = discord.Embed(
                title=f' {info["name"]} \u2764',
                description=f'{info["description"]}',
                colour=Colours.pink
            )
            cdir = Path("/bot/resources/flags/512/afghanistan.png")
            f = discord.File(cdir, filename="image.png")

            embed.set_image(url="attachment://image.png")
            # await messagable.send(file=f, embed=e)

            # embed.set_image(url=open(, "rb").read())

            # print(counter)
            await ctx.channel.send(file=f, embed=embed)

    @commands.command()
    async def inform(self, ctx, *, country_name: str = None):
        """
        Provides the name and info on the country(ies) who's birthday is today, if no country name is provided.
        Provides the independence information about the country provided
        :param ctx: takes in ctx to send data to discord channel
        :param country_name: takes in optional name of a country to provide info on that country
        """
        dates = self.indep_info["dates"]

        if country_name:
            await self.produce_info(ctx, country_name.lower())
        else:
            today = datetime.now()
            month = today.strftime("%B")
            day = str(today.strftime("%d"))

            if day in dates[month]:
                for country_name in dates[month][day]:
                    await self.produce_info(ctx, country_name)
            else:
                output = "Today is one of the lovely days where no country saw their independence, or at least," \
                         " not yet documented"
                await ctx.send(output)


def setup(bot):
    bot.add_cog(CountriesBirth(bot))

# TODO handle naming conventions between files
# TODO handle partial namings of countries
# TODO handle countries not in our list
# TODO test dates make sure country is pulled via dates
# TODO test multiple countries based on dates

import json
import logging
from pathlib import Path
from datetime import datetime
from fuzzywuzzy import process


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

    def get_flag_url(self,country, size=512):
        """Fetch flag by country name and size using defined base URL."""
        flag = "https://raw.githubusercontent.com/jodth07/seasonalbot/global-birth/bot/resources/flags/"
        return f"{flag}{size}/{country}.png"

    # FLAG_URL = "https://raw.githubusercontent.com/python-discord/seasonalbot/master/bot/resources/flags/"  <-- use this for live
    # FLAG = "https://raw.githubusercontent.com/jodth07/seasonalbot/global-birth/bot/resources/flags/"

    def load_data(self):
        """
        Loading the json data to be used for the rest of the class
        :return: loaded json data as dictionary
        """
        indep_file = open(Path("bot", "resources", "evergreen", "global_birth.json"), "r")
        return json.load(indep_file)

    async def produce_info(self, ctx, country_name: str = None):
        """
        Processes the country name against the `countries` dictionary in
        :param ctx: takes in ctx to send data to discord channel
        :param country_name: takes in the name of a country to get it's info
        """
        countries = self.indep_info["countries"]
        for info in countries[country_name]:
            # TODO complete and test embed
            embed = discord.Embed(
                title=f'{info["name"]} \u2764',
                description=f'{info["description"]}',
                colour=Colours.pink
            )

            embed.add_field(name="independence", value=info["independence"])
            embed.add_field(name="holiday", value=info["holiday"])
            embed.set_image(url=self.get_flag_url(country_name))

            # print(counter)
            await ctx.channel.send(embed=embed)

    async def wrong_name(self, ctx, country_name):   #<---- this does not work anywhere in the commands inform aysnc func no matter where i put it in the conditonal
            countries = self.indep_info["countries"].keys()
            country_name = country_name.lower().strip().replace(" ", "_")

            if country_name not in countries:
                a = process.extract(country_name, countries, limit=3)
                b = [i[0:1] for i in a]
                c = " , ".join(b[0] + b[1] + b[2])
                message = f'country name does not exists did you mean? \n{c}'
                await ctx.send(message)


    @commands.command()
    async def inform(self, ctx, *, country_name: str = None):

        # please put the wrong name omewhere in this branch
        """
        Provides the name and info on the country(ies) who's birthday is today, if no country name is provided.
        Provides the independence information about the country provided
        :param ctx: takes in ctx to send data to discord channel
        :param country_name: takes in optional name of a country to provide info on that country
        """
        dates = self.indep_info["dates"]

        if country_name:
            await self.produce_info(ctx, country_name)

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
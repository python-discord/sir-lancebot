import json
import logging
from pathlib import Path

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
        @returns: output the name and info on the country(ies) who's birthday is today.
        @returns: output the independence information about the country provided
        """
        output = f" The country is who knows"
        if country_name:
            output = f" The country is {country_name}"

        await ctx.send(output)


def setup(bot):
    bot.add_cog(CountriesBirth(bot))

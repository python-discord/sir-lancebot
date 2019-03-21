import json
import logging
from pathlib import Path
from random import choice

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)

with open(Path("bot", "resources", "evergreen", "global_birth.json"), "r") as indep_file:
    indep_info = json.load(indep_file)


class CountriesBirth:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=('birthdate'))
    async def independence_date(self, ctx):
        """
        Displays the country(s) whose independence date is today.
        Displays the independence information about a particular country.
        """
        # embed = discord.Embed(
        #     title="Who is Saint Valentine?",
        #     description=FACTS['whois'],
        #     color=Colours.pink
        # )
        # embed.set_thumbnail(
        #     url='https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Saint_Valentine_-_'
        #         'facial_reconstruction.jpg/1024px-Saint_Valentine_-_facial_reconstruction.jpg'
        # )



        await ctx.channel.send()

    # @commands.command()
    # async def valentine_fact(self, ctx):
    #     """
    #     Shows a random fact about Valentine's Day.
    #     """
    #     embed = discord.Embed(
    #         title=choice(FACTS['titles']),
    #         description=choice(FACTS['text']),
    #         color=Colours.pink
    #     )
    #
    #     await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(CountriesBirth(bot))

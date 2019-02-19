import json
import logging
from pathlib import Path
from random import choice

import discord
from discord.ext import commands

log = logging.getLogger(__name__)

with open(Path("bot", "resources", "valentines", "valentine_facts.json"), "r") as file:
    FACTS = json.load(file)


class ValentineFacts:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=('whoisvalentine', 'saint_valentine'))
    async def who_is_valentine(self, ctx):
        """
        Displays info about Saint Valentine.
        """
        embed = discord.Embed(
            title="Who is Saint Valentine?",
            description=FACTS['whois'],
            color=discord.Color.dark_magenta()
        )
        embed.set_thumbnail(
            url='https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Saint_Valentine_-_'
                'facial_reconstruction.jpg/1024px-Saint_Valentine_-_facial_reconstruction.jpg'
        )

        await ctx.channel.send(embed=embed)

    @commands.command()
    async def valentine_facts(self, ctx):
        """
        Shows a random fact about Valentine's Day.
        """
        embed = discord.Embed(
            title=choice(FACTS['titles']),
            description=choice(FACTS['text']),
            color=discord.Color.dark_magenta()
        )

        await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(ValentineFacts(bot))

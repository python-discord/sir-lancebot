import asyncio
import random
from json import load
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Colours


class EasterFacts(commands.Cog):
    """A cog for easter egg facts."""
    def __init__(self, bot):
        self.bot = bot
        self.facts = self.load_json()

    @staticmethod
    def load_json():
        """Loading the json data"""
        p = Path('bot', 'resources', 'easter', 'easter_egg_facts.json')
        with p.open(encoding="utf8") as f:
            facts = load(f)
        return facts

    async def background(self):
        """A background task that sends a easter egg fact."""
        channel = self.bot.get_channel(426566445124812815)
        while True:
            embed = self.make_embed()
            await channel.send(embed=embed)
            await asyncio.sleep(24*60*60)

    @commands.command(name='eggfact', aliases=['fact'])
    async def easter_facts(self, ctx):
        """Get easter egg facts."""
        embed = self.make_embed()
        await ctx.send(embed=embed)

    def make_embed(self):
        """Makes a nice embed for the message to be sent."""
        embed = discord.Embed()
        embed.colour = Colours.soft_red
        embed.title = 'Easter Egg Fact'
        random_fact = random.choice(self.facts)
        embed.description = random_fact
        return embed


def setup(bot):
    """Loading the cog"""
    bot.loop.create_task(EasterFacts(bot).background())
    bot.add_cog(EasterFacts(bot))

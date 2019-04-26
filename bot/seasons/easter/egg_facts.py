import asyncio
import random
from json import load
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Colours


class EasterFacts(commands.Cog):
    """
    A cog contains a command that will return an easter egg fact when called.

    It also contains a background task which sends an easter egg fact in the event channel everyday.
    """

    def __init__(self, bot):
        self.bot = bot
        self.facts = self.load_json()

    @staticmethod
    def load_json():
        """Load a list of easter egg facts from the resource JSON file."""

        p = Path('bot', 'resources', 'easter', 'easter_egg_facts.json')
        with p.open(encoding="utf8") as f:
            facts = load(f)
        return facts

    async def send_egg_fact_daily(self):
        """A background task that sends an easter egg fact in the event channel everyday."""

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
    """EasterEgg facts loaded."""

    bot.loop.create_task(EasterFacts(bot).send_egg_fact_daily())
    bot.add_cog(EasterFacts(bot))

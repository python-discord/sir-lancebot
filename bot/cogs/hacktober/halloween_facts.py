import asyncio
import json
import random
from datetime import timedelta
from pathlib import Path

import discord
from discord.ext import commands

SPOOKY_EMOJIS = [
    "\N{BAT}",
    "\N{DERELICT HOUSE BUILDING}",
    "\N{EXTRATERRESTRIAL ALIEN}",
    "\N{GHOST}",
    "\N{JACK-O-LANTERN}",
    "\N{SKULL}",
    "\N{SKULL AND CROSSBONES}",
    "\N{SPIDER WEB}",
]
PUMPKIN_ORANGE = discord.Color(0xFF7518)
HACKTOBERBOT_CHANNEL_ID = 498804484324196362
INTERVAL = timedelta(hours=6).total_seconds()


class HalloweenFacts:

    def __init__(self, bot):
        self.bot = bot
        with open(Path("./bot/resources", "halloween_facts.json"), "r") as file:
            self.halloween_facts = json.load(file)
        self.channel = None
        self.last_fact = None

    async def on_ready(self):
        self.channel = self.bot.get_channel(HACKTOBERBOT_CHANNEL_ID)
        self.bot.loop.create_task(self._fact_publisher_task())

    async def _fact_publisher_task(self):
        """
        A background task that runs forever, sending Halloween facts at random to the Discord channel with id equal to
        HACKTOBERFEST_CHANNEL_ID every INTERVAL seconds.
        """
        facts = list(enumerate(self.halloween_facts))
        while True:
            # Avoid choosing each fact at random to reduce chances of facts being reposted soon.
            random.shuffle(facts)
            for index, fact in facts:
                embed = self._build_embed(index, fact)
                await self.channel.send("Your regular serving of random Halloween facts", embed=embed)
                self.last_fact = (index, fact)
                await asyncio.sleep(INTERVAL)

    @commands.command(name="hallofact", aliases=["hallofacts"], brief="Get the most recent Halloween fact")
    async def get_last_fact(self, ctx):
        """
        Reply with the most recent Halloween fact.
        """
        if ctx.channel != self.channel:
            return
        index, fact = self.last_fact
        embed = self._build_embed(index, fact)
        await ctx.send("Halloween fact recap", embed=embed)

    @staticmethod
    def _build_embed(index, fact):
        """
        Builds a Discord embed from the given fact and its index.
        """
        emoji = random.choice(SPOOKY_EMOJIS)
        title = f"{emoji} Halloween Fact #{index + 1}"
        return discord.Embed(title=title, description=fact, color=PUMPKIN_ORANGE)


def setup(bot):
    bot.add_cog(HalloweenFacts(bot))

import json
import logging
import random
from datetime import timedelta
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Hacktoberfest

log = logging.getLogger(__name__)

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
INTERVAL = timedelta(hours=6).total_seconds()


class HalloweenFacts:

    def __init__(self, bot):
        self.bot = bot
        with open(Path("bot", "resources", "halloween", "halloween_facts.json"), "r") as file:
            self.halloween_facts = json.load(file)
        self.channel = None
        self.facts = list(enumerate(self.halloween_facts))
        random.shuffle(self.facts)

    async def on_ready(self):
        self.channel = self.bot.get_channel(Hacktoberfest.channel_id)
        self.bot.loop.create_task(self._fact_publisher_task())

    def random_fact(self):
        return random.choice(self.facts)

    @commands.command(name="spookyfact", aliases=("halloweenfact",), brief="Get the most recent Halloween fact")
    async def get_random_fact(self, ctx):
        """
        Reply with the most recent Halloween fact.
        """
        index, fact = self.random_fact()
        embed = self._build_embed(index, fact)
        await ctx.send(embed=embed)

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
    log.debug("HalloweenFacts cog loaded")

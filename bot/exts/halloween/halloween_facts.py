import json
import logging
import random
from datetime import timedelta
from pathlib import Path
from typing import Tuple

import discord
from discord.ext import commands

from bot.constants import Channels

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


class HalloweenFacts(commands.Cog):
    """A Cog for displaying interesting facts about Halloween."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open(Path("bot/resources/halloween/halloween_facts.json"), "r") as file:
            self.halloween_facts = json.load(file)
        self.channel = None
        self.facts = list(enumerate(self.halloween_facts))
        random.shuffle(self.facts)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Get event Channel object and initialize fact task loop."""
        self.channel = self.bot.get_channel(Channels.seasonalbot_commands)
        self.bot.loop.create_task(self._fact_publisher_task())

    def random_fact(self) -> Tuple[int, str]:
        """Return a random fact from the loaded facts."""
        return random.choice(self.facts)

    @commands.command(name="spookyfact", aliases=("halloweenfact",), brief="Get the most recent Halloween fact")
    async def get_random_fact(self, ctx: commands.Context) -> None:
        """Reply with the most recent Halloween fact."""
        index, fact = self.random_fact()
        embed = self._build_embed(index, fact)
        await ctx.send(embed=embed)

    @staticmethod
    def _build_embed(index: int, fact: str) -> discord.Embed:
        """Builds a Discord embed from the given fact and its index."""
        emoji = random.choice(SPOOKY_EMOJIS)
        title = f"{emoji} Halloween Fact #{index + 1}"
        return discord.Embed(title=title, description=fact, color=PUMPKIN_ORANGE)


def setup(bot: commands.Bot) -> None:
    """Halloween facts Cog load."""
    bot.add_cog(HalloweenFacts(bot))
    log.info("HalloweenFacts cog loaded")

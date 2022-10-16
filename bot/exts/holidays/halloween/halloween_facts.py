import json
import logging
import random
from datetime import timedelta
from pathlib import Path

import discord
from discord.ext import commands

from bot.bot import Bot

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
PUMPKIN_ORANGE = 0xFF7518
INTERVAL = timedelta(hours=6).total_seconds()

FACTS = json.loads(Path("bot/resources/holidays/halloween/halloween_facts.json").read_text("utf8"))
FACTS = list(enumerate(FACTS))


class HalloweenFacts(commands.Cog):
    """A Cog for displaying interesting facts about Halloween."""

    def random_fact(self) -> tuple[int, str]:
        """Return a random fact from the loaded facts."""
        return random.choice(FACTS)

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


async def setup(bot: Bot) -> None:
    """Load the Halloween Facts Cog."""
    await bot.add_cog(HalloweenFacts())

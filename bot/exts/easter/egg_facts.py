import asyncio
import logging
import random
from json import load
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Channels
from bot.constants import Colours


log = logging.getLogger(__name__)


class EasterFacts(commands.Cog):
    """
    A cog contains a command that will return an easter egg fact when called.

    It also contains a background task which sends an easter egg fact in the event channel everyday.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.facts = self.load_json()

    @staticmethod
    def load_json() -> dict:
        """Load a list of easter egg facts from the resource JSON file."""
        p = Path("bot/resources/easter/easter_egg_facts.json")
        with p.open(encoding="utf8") as f:
            return load(f)

    async def send_egg_fact_daily(self) -> None:
        """A background task that sends an easter egg fact in the event channel everyday."""
        channel = self.bot.get_channel(Channels.seasonalbot_commands)
        while True:
            embed = self.make_embed()
            await channel.send(embed=embed)
            await asyncio.sleep(24 * 60 * 60)

    @commands.command(name='eggfact', aliases=['fact'])
    async def easter_facts(self, ctx: commands.Context) -> None:
        """Get easter egg facts."""
        embed = self.make_embed()
        await ctx.send(embed=embed)

    def make_embed(self) -> discord.Embed:
        """Makes a nice embed for the message to be sent."""
        return discord.Embed(
            colour=Colours.soft_red,
            title="Easter Egg Fact",
            description=random.choice(self.facts)
        )


def setup(bot: commands.Bot) -> None:
    """Easter Egg facts cog load."""
    bot.loop.create_task(EasterFacts(bot).send_egg_fact_daily())
    bot.add_cog(EasterFacts(bot))
    log.info("EasterFacts cog loaded")

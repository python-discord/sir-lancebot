import logging
import random
from json import load
from pathlib import Path

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Channels, Colours, Month
from bot.utils.decorators import seasonal_task

log = logging.getLogger(__name__)


class EasterFacts(commands.Cog):
    """
    A cog contains a command that will return an easter egg fact when called.

    It also contains a background task which sends an easter egg fact in the event channel everyday.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.facts = self.load_json()

        self.daily_fact_task = self.bot.loop.create_task(self.send_egg_fact_daily())

    @staticmethod
    def load_json() -> dict:
        """Load a list of easter egg facts from the resource JSON file."""
        p = Path("bot/resources/easter/easter_egg_facts.json")
        with p.open(encoding="utf8") as f:
            return load(f)

    @seasonal_task(Month.APRIL)
    async def send_egg_fact_daily(self) -> None:
        """A background task that sends an easter egg fact in the event channel everyday."""
        await self.bot.wait_until_guild_available()

        channel = self.bot.get_channel(Channels.community_bot_commands)
        await channel.send(embed=self.make_embed())

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


def setup(bot: Bot) -> None:
    """Easter Egg facts cog load."""
    bot.add_cog(EasterFacts(bot))

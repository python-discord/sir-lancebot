import logging
import random
from json import loads
from pathlib import Path

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Channels, Colours, Month
from bot.utils.decorators import seasonal_task

log = logging.getLogger(__name__)

EGG_FACTS = loads(Path("bot/resources/holidays/easter/easter_egg_facts.json").read_text("utf8"))


class EasterFacts(commands.Cog):
    """
    A cog contains a command that will return an easter egg fact when called.

    It also contains a background task which sends an easter egg fact in the event channel everyday.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.daily_fact_task = self.bot.loop.create_task(self.send_egg_fact_daily())

    @seasonal_task(Month.APRIL)
    async def send_egg_fact_daily(self) -> None:
        """A background task that sends an easter egg fact in the event channel everyday."""
        channel = self.bot.get_channel(Channels.sir_lancebot_playground)
        await channel.send(embed=self.make_embed())

    @commands.command(name="eggfact", aliases=("fact",))
    async def easter_facts(self, ctx: commands.Context) -> None:
        """Get easter egg facts."""
        embed = self.make_embed()
        await ctx.send(embed=embed)

    @staticmethod
    def make_embed() -> discord.Embed:
        """Makes a nice embed for the message to be sent."""
        return discord.Embed(
            colour=Colours.soft_red,
            title="Easter Egg Fact",
            description=random.choice(EGG_FACTS)
        )


async def setup(bot: Bot) -> None:
    """Load the Easter Egg facts Cog."""
    await bot.add_cog(EasterFacts(bot))

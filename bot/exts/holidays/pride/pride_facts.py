import json
import logging
import random
from datetime import UTC, datetime
from pathlib import Path

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Channels, Colours, Month
from bot.utils.decorators import seasonal_task

log = logging.getLogger(__name__)

FACTS = json.loads(Path("bot/resources/holidays/pride/facts.json").read_text("utf8"))


class PrideFacts(commands.Cog):
    """Provides a new fact every day during the Pride season!"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.daily_fact_task = self.bot.loop.create_task(self.send_pride_fact_daily())

    @seasonal_task(Month.JUNE)
    async def send_pride_fact_daily(self) -> None:
        """Background task to post the daily pride fact every day."""
        channel = self.bot.get_channel(Channels.sir_lancebot_playground)
        await self.send_select_fact(channel, datetime.now(tz=UTC).day)

    async def send_select_fact(self, target: discord.abc.Messageable, day_num: int) -> None:
        """Provides the fact for the specified day."""
        try:
            await target.send(embed=self.get_fact_embed(day_num))
        except IndexError:
            await target.send(f"Day {day_num} is not supported")
            return

    @commands.command(name="pridefact", aliases=("pridefacts",))
    async def pridefact(self, ctx: commands.Context, option: int | str = None) -> None:
        """
        Sends a message with a pride fact of the day.

        "option" is an optional setting, which has two has two accepted values:
          - "random": a random previous fact will be provided.
          - If a option is a number (1-30), the fact for that given day of June is returned.
        """
        if not option:
            await self.send_select_fact(ctx, datetime.now(tz=UTC).day)
        elif isinstance(option, int):
            await self.send_select_fact(ctx, option)
        elif option.lower().startswith("rand"):
            await ctx.send(embed=self.get_fact_embed())
        else:
            await ctx.send(f"Could not parse option {option}")

    @staticmethod
    def get_fact_embed(day_num: int | None=None) -> discord.Embed:
        """
        Makes a embed for the fact on the given day_num to be sent.

        if day_num is not set, a random fact is selected.
        """
        fact = FACTS[day_num-1] if day_num else random.choice(FACTS)
        return discord.Embed(
            colour=Colours.pink,
            title=f"Day {day_num}'s pride fact!" if day_num else "Random pride fact!",
            description=fact
        )


async def setup(bot: Bot) -> None:
    """Load the Pride Facts Cog."""
    await bot.add_cog(PrideFacts(bot))

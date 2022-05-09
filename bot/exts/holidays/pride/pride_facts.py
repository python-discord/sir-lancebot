import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Union

import dateutil.parser
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
        await self.bot.wait_until_guild_available()

        channel = self.bot.get_channel(Channels.sir_lancebot_playground)
        await self.send_select_fact(channel, datetime.utcnow())

    async def send_random_fact(self, ctx: commands.Context) -> None:
        """Provides a fact from any previous day, or today."""
        now = datetime.utcnow()
        previous_years_facts = (y for x, y in FACTS.items() if int(x) < now.year)
        current_year_facts = FACTS.get(str(now.year), [])[:now.day]
        previous_facts = current_year_facts + [x for y in previous_years_facts for x in y]
        try:
            await ctx.send(embed=self.make_embed(random.choice(previous_facts)))
        except IndexError:
            await ctx.send("No facts available")

    async def send_select_fact(self, target: discord.abc.Messageable, _date: Union[str, datetime]) -> None:
        """Provides the fact for the specified day, if the day is today, or is in the past."""
        now = datetime.utcnow()
        if isinstance(_date, str):
            try:
                date = dateutil.parser.parse(_date, dayfirst=False, yearfirst=False, fuzzy=True)
            except (ValueError, OverflowError) as err:
                await target.send(f"Error parsing date: {err}")
                return
        else:
            date = _date
        if date.year < now.year or (date.year == now.year and date.day <= now.day):
            try:
                await target.send(embed=self.make_embed(FACTS[str(date.year)][date.day - 1]))
            except KeyError:
                await target.send(f"The year {date.year} is not yet supported")
                return
            except IndexError:
                await target.send(f"Day {date.day} of {date.year} is not yet support")
                return
        else:
            await target.send("The fact for the selected day is not yet available.")

    @commands.command(name="pridefact", aliases=("pridefacts",))
    async def pridefact(self, ctx: commands.Context, option: str = None) -> None:
        """
        Sends a message with a pride fact of the day.

        If "random" is given as an argument, a random previous fact will be provided.

        If a date is given as an argument, and the date is in the past, the fact from that day
        will be provided.
        """
        if not option:
            await self.send_select_fact(ctx, datetime.utcnow())
        elif option.lower().startswith("rand"):
            await self.send_random_fact(ctx)
        else:
            await self.send_select_fact(ctx, option)

    @staticmethod
    def make_embed(fact: str) -> discord.Embed:
        """Makes a nice embed for the fact to be sent."""
        return discord.Embed(
            colour=Colours.pink,
            title="Pride Fact!",
            description=fact
        )


def setup(bot: Bot) -> None:
    """Load the Pride Facts Cog."""
    bot.add_cog(PrideFacts(bot))

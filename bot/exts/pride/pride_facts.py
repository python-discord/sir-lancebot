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

Sendable = Union[commands.Context, discord.TextChannel]


class PrideFacts(commands.Cog):
    """Provides a new fact every day during the Pride season!"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.facts = self.load_facts()

        self.daily_fact_task = self.bot.loop.create_task(self.send_pride_fact_daily())

    @staticmethod
    def load_facts() -> dict:
        """Loads a dictionary of years mapping to lists of facts."""
        with open(Path("bot/resources/pride/facts.json"), "r", encoding="utf8") as f:
            return json.load(f)

    @seasonal_task(Month.JUNE)
    async def send_pride_fact_daily(self) -> None:
        """Background task to post the daily pride fact every day."""
        await self.bot.wait_until_guild_available()

        channel = self.bot.get_channel(Channels.community_bot_commands)
        await self.send_select_fact(channel, datetime.utcnow())

    async def send_random_fact(self, ctx: commands.Context) -> None:
        """Provides a fact from any previous day, or today."""
        now = datetime.utcnow()
        previous_years_facts = (self.facts[x] for x in self.facts.keys() if int(x) < now.year)
        current_year_facts = self.facts.get(str(now.year), [])[:now.day]
        previous_facts = current_year_facts + [x for y in previous_years_facts for x in y]
        try:
            await ctx.send(embed=self.make_embed(random.choice(previous_facts)))
        except IndexError:
            await ctx.send("No facts available")

    async def send_select_fact(self, target: Sendable, _date: Union[str, datetime]) -> None:
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
                await target.send(embed=self.make_embed(self.facts[str(date.year)][date.day - 1]))
            except KeyError:
                await target.send(f"The year {date.year} is not yet supported")
                return
            except IndexError:
                await target.send(f"Day {date.day} of {date.year} is not yet support")
                return
        else:
            await target.send("The fact for the selected day is not yet available.")

    @commands.command(name="pridefact", aliases=["pridefacts"])
    async def pridefact(self, ctx: commands.Context) -> None:
        """
        Sends a message with a pride fact of the day.

        If "random" is given as an argument, a random previous fact will be provided.

        If a date is given as an argument, and the date is in the past, the fact from that day
        will be provided.
        """
        message_body = ctx.message.content[len(ctx.invoked_with) + 2:]
        if message_body == "":
            await self.send_select_fact(ctx, datetime.utcnow())
        elif message_body.lower().startswith("rand"):
            await self.send_random_fact(ctx)
        else:
            await self.send_select_fact(ctx, message_body)

    def make_embed(self, fact: str) -> discord.Embed:
        """Makes a nice embed for the fact to be sent."""
        return discord.Embed(
            colour=Colours.pink,
            title="Pride Fact!",
            description=fact
        )


def setup(bot: Bot) -> None:
    """Cog loader for pride facts."""
    bot.add_cog(PrideFacts(bot))

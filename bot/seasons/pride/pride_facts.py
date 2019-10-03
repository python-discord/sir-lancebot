from datetime import datetime
import json
import logging
from typing import Union
import random
from pathlib import Path

import dateutil.parser
from discord.ext import commands

log = logging.getLogger(__name__)


class PrideFacts(commands.Cog):
    """Provides a new fact every day during the Pride season!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.facts = self.load_facts()

    @staticmethod
    def load_facts() -> dict:
        """Loads a dictionary of years mapping to lists of facts."""
        with open(Path("bot/resources/pride/facts.json"), "r", encoding="utf-8") as f:
            return json.load(f)

    async def random_fact(self, ctx: commands.Context):
        """Provides a fact from any valid day."""
        now = datetime.utcnow()
        previous_years_facts = (self.facts[x] for x in self.facts.keys() if int(x) < now.year)
        current_year_facts = self.facts.get(str(now.year), [])[:now.day]
        previous_facts = current_year_facts + [x for y in previous_years_facts for x in y]
        try:
            await ctx.send(random.choice(previous_facts))
        except IndexError:
            await ctx.send("No facts available")

    async def select_fact(self, ctx: commands.Context, _date: Union[str, datetime]):
        """Provides the fact for the specified day, if valid."""
        now = datetime.utcnow()
        if isinstance(_date, str):
            try:
                date = dateutil.parser.parse(_date, dayfirst=False, yearfirst=False, fuzzy=True)
            except (ValueError, OverflowError) as err:
                await ctx.send(f"Error parsing date: {err}")
                return
        else:
            date = _date
        if date.year < now.year or (date.year == now.year and date.day <= now.day):
            try:
                await ctx.send(self.facts[str(date.year)][date.day - 1])
            except KeyError:
                await ctx.send(f"The year {date.year} is not yet supported")
                return
            except IndexError:
                await ctx.send(f"Day {date.day} of {date.year} is not yet support")
                return
        else:
            await ctx.send("The fact for the selected day is not yet available.")

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
            await self.select_fact(ctx, datetime.utcnow())
        elif message_body.lower().startswith("rand"):
            await self.random_fact(ctx)
        else:
            await self.select_fact(ctx, message_body)


def setup(bot: commands.Bot) -> None:
    """Cog loader for pride facts."""
    bot.add_cog(PrideFacts(bot))
    log.info("Pride facts cog loaded!")

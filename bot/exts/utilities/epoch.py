from discord.ext import commands
from discord.ext.commands import Converter
from bot.bot import Bot
from typing import Union

import dateutil
from dateutil import parser
import arrow


class RelativeDate(Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> arrow.Arrow:
        return arrow.utcnow().dehumanize(argument)


class AbsoluteDate(Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> arrow.Arrow:
        return arrow.get(dateutil.parser.parse(argument))


class Epoch(commands.Cog):

    @commands.command(name="epoch")
    async def epoch(self, ctx: commands.Context, *, time: Union[RelativeDate, AbsoluteDate]) -> None:
        pass


def setup(bot: Bot) -> None:
    bot.add_cog(Epoch())

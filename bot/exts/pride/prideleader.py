import json
import logging
from pathlib import Path
from typing import Dict

import discord
from discord.ext import commands

from bot.constants import Colours
log = logging.getLogger(__name__)


class PrideLeader(commands.Cog):
    """Gives a Pride Leader Info."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pride = self.load_json()

    @staticmethod
    def load_json() -> Dict:
        """Loads pride leader information from static json resource."""
        explanation_file = Path("bot/resources/pride/prideleader.json")
        with explanation_file.open(encoding="utf8") as json_data:
            pride = json.load(json_data)

        return pride

    @commands.command(name="prideleader", aliases=['pl'])
    async def pl(self, ctx: commands.Context, *, pl: str) -> None:
        """Provides information about pride leader by taking pride leader name as input."""
        embed = discord.Embed()
        embed.color = Colours.blue
        pl = pl.split(" ")
        pl = ' '.join(i.capitalize() for i in pl)
        if pl in self.pride:
            embed.title = f'__{pl}__'
            embed.description = self.pride[pl]["About"]
            embed.add_field(name="__Known for__", value=self.pride[pl]["Known for"], inline=False)
            embed.add_field(name="__D.O.B and Birth place__", value=self.pride[pl]["Born"], inline=False)
            embed.add_field(name="__Awards and honors__", value=self.pride[pl]["Awards"], inline=False)
            embed.set_thumbnail(url=self.pride[pl]["url"])
        else:
            embed.description = "Sorry but i dont know about him"
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Cog loader for drag queen name generator."""
    bot.add_cog(PrideLeader(bot))

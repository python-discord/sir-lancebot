import random
from json import loads
from pathlib import Path

import discord
from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import Colours

log = get_logger(__name__)

HEART_EMOJIS = [":heart:", ":gift_heart:", ":revolving_hearts:", ":sparkling_heart:", ":two_hearts:"]

VALENTINES_DATES = loads(Path("bot/resources/holidays/valentines/date_ideas.json").read_text("utf8"))


class SaveTheDate(commands.Cog):
    """A cog that gives random suggestion for a Valentine's date."""

    @commands.command()
    async def savethedate(self, ctx: commands.Context) -> None:
        """Gives you ideas for what to do on a date with your valentine."""
        random_date = random.choice(VALENTINES_DATES["ideas"])
        emoji_1 = random.choice(HEART_EMOJIS)
        emoji_2 = random.choice(HEART_EMOJIS)
        embed = discord.Embed(
            title=f"{emoji_1}{random_date['name']}{emoji_2}",
            description=f"{random_date['description']}",
            colour=Colours.pink
        )
        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the Save the date Cog."""
    await bot.add_cog(SaveTheDate())

import logging
import random
from json import load
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)

HEART_EMOJIS = [":heart:", ":gift_heart:", ":revolving_hearts:", ":sparkling_heart:", ":two_hearts:"]

with open(Path("bot/resources/valentines/date_ideas.json"), "r", encoding="utf8") as f:
    VALENTINES_DATES = load(f)


class SaveTheDate(commands.Cog):
    """A cog that gives random suggestion for a Valentine's date."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def savethedate(self, ctx: commands.Context) -> None:
        """Gives you ideas for what to do on a date with your valentine."""
        random_date = random.choice(VALENTINES_DATES['ideas'])
        emoji_1 = random.choice(HEART_EMOJIS)
        emoji_2 = random.choice(HEART_EMOJIS)
        embed = discord.Embed(
            title=f"{emoji_1}{random_date['name']}{emoji_2}",
            description=f"{random_date['description']}",
            colour=Colours.pink
        )
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Save the date Cog Load."""
    bot.add_cog(SaveTheDate(bot))
    log.info("SaveTheDate cog loaded")

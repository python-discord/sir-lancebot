import logging
import random
from json import load
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)

HEART_EMOJIS = [":heart:", ":gift_heart:", ":revolving_hearts:", ":sparkling_heart:", ":two_hearts:"]


class SaveTheDate:
    """
    A cog that gives random suggestion, for a valentines date !
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def savethedate(self, ctx):
        """
        Gives you ideas for what to do on a date with your valentine.
        """
        with open(Path('bot', 'resources', 'valentines', 'date_ideas.json'), 'r', encoding="utf8") as f:
            valentine_dates = load(f)
            random_date = random.choice(valentine_dates['ideas'])
            emoji_1 = random.choice(HEART_EMOJIS)
            emoji_2 = random.choice(HEART_EMOJIS)
            embed = discord.Embed(
                title=f"{emoji_1}{random_date['name']}{emoji_2}",
                description=f"{random_date['description']}",
                colour=Colours.pink
            )
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(SaveTheDate(bot))
    log.debug("Save the date cog loaded")

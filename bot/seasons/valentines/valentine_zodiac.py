import logging
import random
from json import load
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)

LETTER_EMOJI = ':love_letter:'
HEART_EMOJIS = [":heart:", ":gift_heart:", ":revolving_hearts:", ":sparkling_heart:", ":two_hearts:"]


class ValentineZodiac:
    """
    A cog that returns a counter compatible zodiac sign to the given user's zodiac sign.
    """
    def __init__(self, bot):
        self.bot = bot
        self.zodiacs = self.load_json()

    @staticmethod
    def load_json():
        p = Path('bot', 'resources', 'valentines', 'zodiac_compatibility.json')
        with p.open() as json_data:
            zodiacs = load(json_data)
            return zodiacs

    @commands.command(name="partnerzodiac")
    async def counter_zodiac(self, ctx, zodiac_sign):
        """
        Provides a counter compatible zodiac sign to the given user's zodiac sign.
        """
        try:
            compatible_zodiac = random.choice(self.zodiacs[zodiac_sign.lower()])
        except KeyError:
            return await ctx.send(zodiac_sign.capitalize() + " zodiac sign does not exist.")

        emoji1 = random.choice(HEART_EMOJIS)
        emoji2 = random.choice(HEART_EMOJIS)
        embed = discord.Embed(
            title="Zodic Compatibility",
            description=f'{zodiac_sign.capitalize()}{emoji1}{compatible_zodiac["Zodiac"]}\n'
                        f'{emoji2}Compatibility meter : {compatible_zodiac["compatibility_score"]}{emoji2}',
            color=Colours.pink
        )
        embed.add_field(
            name=f'A letter from Dr.Zodiac {LETTER_EMOJI}',
            value=compatible_zodiac['description']
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ValentineZodiac(bot))
    log.debug("Valentine Zodiac cog loaded")

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

    @commands.command(name="partnerzodiac")
    async def counter_zodiac(self, ctx, zodiac_sign):
        """
        Provides a counter compatible zodiac sign to the given user's zodiac sign.
        """
        try:
            with open(Path('bot', 'resources', 'valentines', 'zodiac_compatibility.json'), 'r', encoding="utf8") as f:
                zodiacs = load(f)
                compatible_zodiac = random.choice(zodiacs[zodiac_sign.lower()])
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
        except Exception as e:
            if isinstance(e, KeyError):
                await ctx.send(zodiac_sign.capitalize() + " zodiac sign does not exist.")
            else:
                raise e


def setup(bot):
    bot.add_cog(ValentineZodiac(bot))
    log.debug("Save the date cog loaded")

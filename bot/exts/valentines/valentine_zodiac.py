import logging
import random
from datetime import datetime
from json import load
from pathlib import Path
from typing import Union

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)

LETTER_EMOJI = ':love_letter:'
HEART_EMOJIS = [":heart:", ":gift_heart:", ":revolving_hearts:", ":sparkling_heart:", ":two_hearts:"]

ZODIAC_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
                "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

MONTH_NAME = {"January": 1, "Jan": 1, "February": 2, "Feb": 2, "March": 3, "Mar": 3,
              "April": 4, "Apr": 4, "May": 5, "June": 6, "Jun": 6, "July": 7, "Jul": 7,
              "August": 8, "Aug": 8, "September": 9, "Sept": 9, "October": 10, "Oct": 10,
              "November": 11, "Nov": 11, "December": 12, "Dec": 12
              }


class ValentineZodiac(commands.Cog):
    """A Cog that returns a counter compatible zodiac sign to the given user's zodiac sign."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.zodiacs, self.zodiac_fact = self.load_comp_json()

    @staticmethod
    def load_comp_json() -> dict:
        """Load zodiac compatibility from static JSON resource."""
        explanation_file = Path("bot/resources/valentines/zodiac_explanation.json")
        compatibility_file = Path("bot/resources/valentines/zodiac_compatibility.json")
        with explanation_file.open(encoding="utf8") as json_data:
            zodiac_fact = load(json_data)
        with compatibility_file.open(encoding="utf8") as json_data:
            zodiacs = load(json_data)
            return zodiacs, zodiac_fact

    def zodiac_sign_verify(self, zodiac: str) -> discord.Embed:
        """Gives informative zodiac embed."""
        zodiac = zodiac.capitalize()
        zodiac_fact = self.zodiac_fact
        embed = discord.Embed()
        embed.color = Colours.pink
        if zodiac in self.zodiac_fact:
            log.info("Making zodiac embed")
            embed.title = f"__{zodiac}__"
            embed.description = zodiac_fact[f"{zodiac}"]["About"]
            embed.add_field(name='__Full form__', value=zodiac_fact[f"{zodiac}"]["full_form"], inline=False)
            embed.add_field(name='__Motto__', value=zodiac_fact[f"{zodiac}"]["Motto"], inline=False)
            embed.add_field(name='__Strengths__', value=zodiac_fact[f"{zodiac}"]["Strengths"], inline=False)
            embed.add_field(name='__Weaknesses__', value=zodiac_fact[f"{zodiac}"]["Weaknesses"], inline=False)
            embed.set_thumbnail(url=zodiac_fact[f"{zodiac}"]["url"])
        else:
            embed.description = "Umm you gave wrong zodiac name so i aren't able to find any :sweat_smile:"
            log.info("Wrong Zodiac name provided")
        log.info("Zodiac embed ready")
        return embed

    def zodiac_date_verifer(self, query_datetime: datetime) -> str:
        """Returns zodiac sign by checking month and date."""
        for zodiac_name, zodiac_data in self.zodiac_fact.items():
            if zodiac_data["start_at"] <= query_datetime.date() <= zodiac_data["end_at"]:
                zodiac = zodiac_name
                break
            else:
                zodiac = None
                log.info("Wrong Zodiac date or month provided")
        log.info("Zodiac name sent")
        return zodiac

    @commands.group(name='zodiac', invoke_without_command=True)
    async def zodiac(self, ctx: commands.Context, zodiac_sign: str) -> None:
        """Provides information about zodiac sign by taking zodiac sign name as input."""
        final_embed = self.zodiac_sign_verify(zodiac_sign)
        log.info("Embed successfully sent")
        await ctx.send(embed=final_embed)

    @zodiac.command(name="date")
    async def date_and_month(self, ctx: commands.Context, date: int, month: Union[int, str]) -> None:
        """Provides information about zodiac sign by taking month and date as input."""
        if isinstance(month, str):
            month = month.capitalize()
            try:
                month = list(calendar.month_abbr).index(month[:3])
            except ValueError:
                await ctx.send("Sorry, but you have given wrong month name.")
                return
        if (month == 1 and (1 <= date <= 19)) or (month == 12 and (22 <= date <= 31)):
            zodiac = "capricorn"
            final_embed = self.zodiac_sign_verify(zodiac)
        else:
            try:
                zodiac_sign_based_on_month_and_date = self.zodiac_date_verifer(datetime(2020, month, date))
                log.info("zodiac sign based on month and date received")
            except ValueError as e:
                log.info("zodiac sign based on month and date returned None")
                final_embed = discord.Embed()
                final_embed.color = Colours.pink
                final_embed.description = f"{e}, cannot find zodiac sign."
            else:
                final_embed = self.zodiac_sign_verify(zodiac_sign_based_on_month_and_date)
                log.info("zodiac sign embed based on month and date is now sent.")

        await ctx.send(embed=final_embed)

    @zodiac.command(name="partnerzodiac")
    async def partner_zodiac(self, ctx: commands.Context, zodiac_sign: str) -> None:
        """Provides a counter compatible zodiac sign to the given user's zodiac sign."""
        try:
            compatible_zodiac = random.choice(self.zodiacs[zodiac_sign.lower()])
        except KeyError:
            await ctx.send(f"`{zodiac_sign.capitalize()}` zodiac sign does not exist.")
            return

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


def setup(bot: commands.Bot) -> None:
    """Valentine zodiac Cog load."""
    bot.add_cog(ValentineZodiac(bot))

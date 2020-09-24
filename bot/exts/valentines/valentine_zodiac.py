import logging
import random
from datetime import datetime
from json import load
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)

LETTER_EMOJI = ':love_letter:'
HEART_EMOJIS = [":heart:", ":gift_heart:", ":revolving_hearts:", ":sparkling_heart:", ":two_hearts:"]

ZODIAC_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
                "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


class ValentineZodiac(commands.Cog):
    """A Cog that returns a counter compatible zodiac sign to the given user's zodiac sign."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.zodiacs, self.zodiac_fact = self.load_comp_json()

    @staticmethod
    def load_comp_json() -> dict:
        """Load zodiac compatibility from static JSON resource."""
        p1 = Path("bot/resources/valentines/zodiac_explanation.json")
        p = Path("bot/resources/valentines/zodiac_compatibility.json")
        with p1.open(encoding="utf8") as json_data:
            zodiac_fact = load(json_data)
        with p.open(encoding="utf8") as json_data:
            zodiacs = load(json_data)
            return zodiacs, zodiac_fact

    def zodiac_sign_verify(self, zodiac: str) -> discord.Embed:
        """Gives informative zodiac embed."""
        c_zodiac = zodiac.capitalize()
        zodiac_fact = self.zodiac_fact
        embed = discord.Embed()
        embed.color = Colours.pink
        if c_zodiac in ZODIAC_SIGNS:
            log.info("Making zodiac embed")
            embed.title = f"__{c_zodiac}__"
            embed.description = zodiac_fact[f"{c_zodiac}"]["About"]
            embed.add_field(name='__Full form__', value=zodiac_fact[f"{c_zodiac}"]["full_form"], inline=False)
            embed.add_field(name='__Motto__', value=zodiac_fact[f"{c_zodiac}"]["Motto"], inline=False)
            embed.add_field(name='__Strengths__', value=zodiac_fact[f"{c_zodiac}"]["Strengths"], inline=False)
            embed.add_field(name='__Weaknesses__', value=zodiac_fact[f"{c_zodiac}"]["Weaknesses"], inline=False)
            embed.set_thumbnail(url=zodiac_fact[f"{c_zodiac}"]["url"])
        else:
            embed.description = "Umm you gave wrong zodiac name so i aren't able to find any :sweat_smile:"
            log.info("Wrong Zodiac name provided")
        return embed
        log.info("Zodiac embed ready")

    def zodiac_date_verifer(self, query_datetime: datetime) -> str:
        """Returns zodiac sign by checking month and date."""
        for zodiac_name, date_range in self.zodiac_fact.items():
            value_start = datetime(2020, date_range["start_at"][0], date_range["start_at"][1]).date()
            value_end = datetime(2020, date_range["end_at"][0], date_range["end_at"][1]).date()
            if value_start <= query_datetime.date() <= value_end:
                zodiac = zodiac_name
                break
            else:
                zodiac = None
        log.info("Wrong Zodiac date or month provided")
        return zodiac
        log.info("Zodiac name sent")

    @commands.group(name="partnerzodiac", invoke_without_command=True)
    async def partner_zodiac(self, ctx: commands.Context, zodiac_sign: str) -> None:
        """Provides a counter compatible zodiac sign to the given user's zodiac sign."""
        try:
            compatible_zodiac = random.choice(self.zodiacs[zodiac_sign.lower()])
        except KeyError:
            return await ctx.send(f"`{zodiac_sign.capitalize()}` zodiac sign does not exist.")

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

    @partner_zodiac.command(name='zodiac')
    async def zodiac(self, ctx: commands.Context, zodiac_sign: str) -> None:
        """Provides information about zodiac sign by taking zodiac sign name as input."""
        final_embed = self.zodiac_sign_verify(zodiac_sign)
        log.info("Embed successfully sent")
        await ctx.send(embed=final_embed)

    @partner_zodiac.command(name="date")
    async def date_and_month(self, ctx: commands.Context, month: int, date: int) -> None:
        """Provides information about zodiac sign by taking month and date as input."""
        try:
            zodiac_sign_based_on_month_and_date = self.zodiac_date_verifer(datetime(2020, month, date))
            log.info("zodiac sign based on month and date received")
        except ValueError as e:
            await ctx.send(f'You cannot do that, {e}')
        if zodiac_sign_based_on_month_and_date is None:
            log.info("zodiac sign based on month and date returned None")
            final_embed = discord.Embed()
            final_embed.color = Colours.pink
            final_embed.description = "You provided wrong date or month so i aren't able to find any zodiac sign"
        else:
            final_embed = self.zodiac_sign_verify(zodiac_sign_based_on_month_and_date)
            log.info("zodiac sign embed based on month and date is now sent")
        await ctx.send(embed=final_embed)


def setup(bot: commands.Bot) -> None:
    """Valentine zodiac Cog load."""
    bot.add_cog(ValentineZodiac(bot))

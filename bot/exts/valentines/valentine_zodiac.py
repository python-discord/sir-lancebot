import calendar
import logging
import random
from datetime import date
from json import load
from pathlib import Path
from typing import Tuple, Union

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)

LETTER_EMOJI = ':love_letter:'
HEART_EMOJIS = [":heart:", ":gift_heart:", ":revolving_hearts:", ":sparkling_heart:", ":two_hearts:"]


class ValentineZodiac(commands.Cog):
    """A Cog that returns a counter compatible zodiac sign to the given user's zodiac sign."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.zodiacs, self.zodiac_fact = self.load_comp_json()

    @staticmethod
    def load_comp_json() -> Tuple[dict, dict]:
        """Load zodiac compatibility from static JSON resource."""
        explanation_file = Path("bot/resources/valentines/zodiac_explanation.json")
        compatibility_file = Path("bot/resources/valentines/zodiac_compatibility.json")
        with explanation_file.open(encoding="utf8") as json_data:
            zodiac_fact = load(json_data)
            for zodiac_data in zodiac_fact.values():
                zodiac_data['start_at'] = date.fromisoformat(zodiac_data['start_at'])
                zodiac_data['end_at'] = date.fromisoformat(zodiac_data['end_at'])
        with compatibility_file.open(encoding="utf8") as json_data:
            zodiacs = load(json_data)
        return zodiacs, zodiac_fact

    def zodiac_sign_verify(self, zodiac: str) -> discord.Embed:
        """Gives informative zodiac embed."""
        zodiac = zodiac.capitalize()
        embed = discord.Embed()
        embed.color = Colours.pink
        if zodiac.capitalize() in self.zodiac_fact:
            log.info("Making zodiac embed")
            embed.title = f"__{zodiac}__"
            embed.description = self.zodiac_fact[zodiac]["About"]
            embed.add_field(name='__Full form__', value=self.zodiac_fact[zodiac]["full_form"], inline=False)
            embed.add_field(name='__Motto__', value=self.zodiac_fact[zodiac]["Motto"], inline=False)
            embed.add_field(name='__Strengths__', value=self.zodiac_fact[zodiac]["Strengths"], inline=False)
            embed.add_field(name='__Weaknesses__', value=self.zodiac_fact[zodiac]["Weaknesses"], inline=False)
            embed.set_thumbnail(url=self.zodiac_fact[zodiac]["url"])
        else:
            err_comp = [f"`{i}` {zod_name}" for i, zod_name in enumerate(self.zodiac_fact.keys(), start=1)]
            error = ("\n").join(err_comp)
            error_msg = f"**{zodiac}** is not a valid zodiac sign, here is the list of valid zodiac signs."
            embed.description = f"{error_msg}\n{error}"
            log.info("Wrong Zodiac name provided")
        log.info("Zodiac embed ready")
        return embed

    def zodiac_date_verifier(self, query_datetime: date) -> str:
        """Returns zodiac sign by checking month and date."""
        for zodiac_name, zodiac_data in self.zodiac_fact.items():
            if zodiac_data["start_at"] <= query_datetime <= zodiac_data["end_at"]:
                zodiac = zodiac_name
        log.info("Zodiac name sent")
        return zodiac

    @commands.group(name='zodiac', invoke_without_command=True)
    async def zodiac(self, ctx: commands.Context, zodiac_sign: str) -> None:
        """Provides information about zodiac sign by taking zodiac sign name as input."""
        final_embed = self.zodiac_sign_verify(zodiac_sign)
        log.info("Embed successfully sent")
        await ctx.send(embed=final_embed)

    @zodiac.command(name="date")
    async def date_and_month(self, ctx: commands.Context, query_date: int, month: Union[int, str]) -> None:
        """Provides information about zodiac sign by taking month and date as input."""
        if isinstance(month, str):
            try:
                month = month.capitalize()
                month = list(calendar.month_abbr).index(month[:3])
            except ValueError:
                await ctx.send(f"Sorry, but `{month}` is wrong month name.")
                return
        if (month == 1 and (1 <= date <= 19)) or (month == 12 and (22 <= date <= 31)):
            zodiac = "capricorn"
            final_embed = self.zodiac_sign_verify(zodiac)
        else:
            try:
                zodiac_sign_based_on_month_and_date = self.zodiac_date_verifier(date(2020, month, query_date))
                log.info("zodiac sign based on month and date received")
            except ValueError as e:
                log.info("invalid date or month given")
                final_embed = discord.Embed()
                final_embed.color = Colours.pink
                final_embed.description = f"Zodiac sign is not found because, {e}"
                log.info(e)
            else:
                final_embed = self.zodiac_sign_verify(zodiac_sign_based_on_month_and_date)
                log.info("zodiac sign embed based on month and date is now sent.")

        await ctx.send(embed=final_embed)

    @zodiac.command(name="partnerzodiac")
    async def partner_zodiac(self, ctx: commands.Context, zodiac_sign: str) -> None:
        """Provides a counter compatible zodiac sign to the given user's zodiac sign."""
        embed = discord.Embed()
        embed.color = Colours.pink
        try:
            compatible_zodiac = random.choice(self.zodiacs[zodiac_sign.lower()])
            emoji1 = random.choice(HEART_EMOJIS)
            emoji2 = random.choice(HEART_EMOJIS)
            embed.title = "Zodiac Compatibility"
            embed.description = f"""{zodiac_sign.capitalize()}{emoji1}{compatible_zodiac["Zodiac"]}
                            {emoji2}Compatibility meter : {compatible_zodiac["compatibility_score"]}{emoji2}"""
            embed.add_field(
                name=f'A letter from Dr.Zodiac {LETTER_EMOJI}',
                value=compatible_zodiac['description']
            )
        except KeyError:
            err_comp = [f"`{i}` {zod_name}" for i, zod_name in enumerate(self.zodiac_fact.keys(), start=1)]
            error = ("\n").join(err_comp)
            error_msg = f"**{zodiac_sign}** is not a valid zodiac sign, here is the list of valid zodiac signs."
            embed.description = f"{error_msg}\n{error}"
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Valentine zodiac Cog load."""
    bot.add_cog(ValentineZodiac(bot))

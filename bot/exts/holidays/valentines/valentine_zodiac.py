import calendar
import json
import logging
import random
from datetime import UTC, datetime
from pathlib import Path

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

log = logging.getLogger(__name__)

LETTER_EMOJI = ":love_letter:"
HEART_EMOJIS = [":heart:", ":gift_heart:", ":revolving_hearts:", ":sparkling_heart:", ":two_hearts:"]


class ValentineZodiac(commands.Cog):
    """A Cog that returns a counter compatible zodiac sign to the given user's zodiac sign."""

    def __init__(self):
        self.zodiacs, self.zodiac_fact = self.load_comp_json()

    @staticmethod
    def load_comp_json() -> tuple[dict, dict]:
        """Load zodiac compatibility from static JSON resource."""
        explanation_file = Path("bot/resources/holidays/valentines/zodiac_explanation.json")
        compatibility_file = Path("bot/resources/holidays/valentines/zodiac_compatibility.json")

        zodiac_fact = json.loads(explanation_file.read_text("utf8"))

        for zodiac_data in zodiac_fact.values():
            zodiac_data["start_at"] = datetime.fromisoformat(zodiac_data["start_at"])
            zodiac_data["end_at"] = datetime.fromisoformat(zodiac_data["end_at"])

        zodiacs = json.loads(compatibility_file.read_text("utf8"))

        return zodiacs, zodiac_fact

    def generate_invalidname_embed(self, zodiac: str) -> discord.Embed:
        """Returns error embed."""
        embed = discord.Embed()
        embed.color = Colours.soft_red
        error_msg = f"**{zodiac}** is not a valid zodiac sign, here is the list of valid zodiac signs.\n"
        names = list(self.zodiac_fact)
        middle_index = len(names) // 2
        first_half_names = ", ".join(names[:middle_index])
        second_half_names = ", ".join(names[middle_index:])
        embed.description = error_msg + first_half_names + ",\n" + second_half_names
        log.info("Invalid zodiac name provided.")
        return embed

    def zodiac_build_embed(self, zodiac: str) -> discord.Embed:
        """Gives informative zodiac embed."""
        zodiac = zodiac.capitalize()
        embed = discord.Embed()
        embed.color = Colours.pink
        if zodiac in self.zodiac_fact:
            log.trace("Making zodiac embed.")
            embed.title = f"__{zodiac}__"
            embed.description = self.zodiac_fact[zodiac]["About"]
            embed.add_field(name="__Motto__", value=self.zodiac_fact[zodiac]["Motto"], inline=False)
            embed.add_field(name="__Strengths__", value=self.zodiac_fact[zodiac]["Strengths"], inline=False)
            embed.add_field(name="__Weaknesses__", value=self.zodiac_fact[zodiac]["Weaknesses"], inline=False)
            embed.add_field(name="__Full form__", value=self.zodiac_fact[zodiac]["full_form"], inline=False)
            embed.set_thumbnail(url=self.zodiac_fact[zodiac]["url"])
        else:
            embed = self.generate_invalidname_embed(zodiac)
        log.trace("Successfully created zodiac information embed.")
        return embed

    def zodiac_date_verifier(self, query_date: datetime) -> str:
        """Returns zodiac sign by checking date."""
        for zodiac_name, zodiac_data in self.zodiac_fact.items():
            if zodiac_data["start_at"].date() <= query_date.date() <= zodiac_data["end_at"].date():
                log.trace("Zodiac name sent.")
                return zodiac_name
        return None

    @commands.group(name="zodiac", invoke_without_command=True)
    async def zodiac(self, ctx: commands.Context, zodiac_sign: str) -> None:
        """Provides information about zodiac sign by taking zodiac sign name as input."""
        final_embed = self.zodiac_build_embed(zodiac_sign)
        await ctx.send(embed=final_embed)
        log.trace("Embed successfully sent.")

    @zodiac.command(name="date")
    async def date_and_month(self, ctx: commands.Context, date: int, month: int | str) -> None:
        """Provides information about zodiac sign by taking month and date as input."""
        if isinstance(month, str):
            month = month.capitalize()
            try:
                month = list(calendar.month_abbr).index(month[:3])
                log.trace("Valid month name entered by user")
            except ValueError:
                log.info("Invalid month name entered by user")
                await ctx.send(f"Sorry, but `{month}` is not a valid month name.")
                return
        if (month == 1 and 1 <= date <= 19) or (month == 12 and 22 <= date <= 31):
            zodiac = "capricorn"
            final_embed = self.zodiac_build_embed(zodiac)
        else:
            try:
                zodiac_sign_based_on_date = self.zodiac_date_verifier(datetime(2020, month, date, tzinfo=UTC))
                log.trace("zodiac sign based on month and date received.")
            except ValueError as e:
                final_embed = discord.Embed()
                final_embed.color = Colours.soft_red
                final_embed.description = f"Zodiac sign could not be found because.\n```\n{e}\n```"
                log.info(f"Error in 'zodiac date' command:\n{e}.")
            else:
                final_embed = self.zodiac_build_embed(zodiac_sign_based_on_date)

        await ctx.send(embed=final_embed)
        log.trace("Embed from date successfully sent.")

    @zodiac.command(name="partnerzodiac", aliases=("partner",))
    async def partner_zodiac(self, ctx: commands.Context, zodiac_sign: str) -> None:
        """Provides a random counter compatible zodiac sign to the given user's zodiac sign."""
        embed = discord.Embed()
        embed.color = Colours.pink
        zodiac_check = self.zodiacs.get(zodiac_sign.capitalize())
        if zodiac_check:
            compatible_zodiac = random.choice(self.zodiacs[zodiac_sign.capitalize()])
            emoji1 = random.choice(HEART_EMOJIS)
            emoji2 = random.choice(HEART_EMOJIS)
            embed.title = "Zodiac Compatibility"
            embed.description = (
                f"{zodiac_sign.capitalize()}{emoji1}{compatible_zodiac['Zodiac']}\n"
                f"{emoji2}Compatibility meter : {compatible_zodiac['compatibility_score']}{emoji2}"
            )
            embed.add_field(
                name=f"A letter from Dr.Zodiac {LETTER_EMOJI}",
                value=compatible_zodiac["description"]
            )
        else:
            embed = self.generate_invalidname_embed(zodiac_sign)
        await ctx.send(embed=embed)
        log.trace("Embed from date successfully sent.")


async def setup(bot: Bot) -> None:
    """Load the Valentine zodiac Cog."""
    await bot.add_cog(ValentineZodiac())

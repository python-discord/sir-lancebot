import logging
from typing import Literal

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

log = logging.getLogger(__name__)
BASE_URLS = {
    "png": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/",
    "svg": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/svg/",
}


class Twemoji(commands.Cog):
    """Utilities for working with Twemojis."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def get_url(codepoint: str, format: Literal["png", "svg"]) -> str:
        return f"{BASE_URLS[format]}{codepoint}.{format}"

    @staticmethod
    def build_embed(codepoint: str) -> discord.Embed:
        embed = discord.Embed(
            title="Twemoji",
            description=f"[Download svg]({Twemoji.get_url(codepoint, 'svg')})",
            colour=Colours.twitter_blue,
        )
        embed.set_thumbnail(url=Twemoji.get_url(codepoint, "png"))
        embed.set_footer(text=codepoint)

        return embed

    @commands.command(aliases=("tw",))
    async def twemoji(self, ctx: commands.Context, emoji: str) -> None:
        await ctx.send(embed=self.build_embed(emoji))


def setup(bot: Bot) -> None:
    """Load the Twemoji cog."""
    bot.add_cog(Twemoji(bot))

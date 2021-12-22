import logging
import re
from typing import List, Literal

import discord
from discord.ext import commands
from emoji import is_emoji, UNICODE_EMOJI_ENGLISH


from bot.bot import Bot
from bot.constants import Colours
from bot.utils.extensions import invoke_help_command

log = logging.getLogger(__name__)
BASE_URLS = {
    "png": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/",
    "svg": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/svg/",
}
CODE = re.compile(r"[a-f1-9][a-f0-9]{3,5}$")


class Twemoji(commands.Cog):
    """Utilities for working with Twemojis."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def get_url(codepoint: str, format: Literal["png", "svg"]) -> str:
        return f"{BASE_URLS[format]}{codepoint}.{format}"

    @staticmethod
    def alias_to_name(alias: str) -> str:
        name = alias[1:-1].replace("_", " ")
        return name.capitalize()

    @staticmethod
    def build_embed(codepoint: str) -> discord.Embed:
        emoji = "".join(Twemoji.emoji(e) for e in codepoint.split("-"))

        embed = discord.Embed(
            title=Twemoji.alias_to_name(UNICODE_EMOJI_ENGLISH[emoji]),
            description=f"{codepoint.replace('-', ' ')}\n[Download svg]({Twemoji.get_url(codepoint, 'svg')})",
            colour=Colours.twitter_blue,
        )
        embed.set_thumbnail(url=Twemoji.get_url(codepoint, "png"))
        return embed

    @staticmethod
    def emoji(codepoint: str) -> str:
        if code := Twemoji.trim_code(codepoint):
            return chr(int(code, 16))
        return ""

    @staticmethod
    def codepoint(emoji: str) -> str:
        return hex(ord(emoji))[2:]

    @staticmethod
    def trim_code(codepoint: str) -> str:
        if code := CODE.search(str(codepoint)):
            return code.group()

    def codepoint_from_input(self, raw_emoji: List[str]):
        if is_emoji(raw_emoji[0]):
            emojis = (self.codepoint(emoji) for emoji in raw_emoji[0])
            return "-".join(emojis)

        raw_first = self.trim_code(raw_emoji[0])
        if is_emoji("".join(self.emoji(self.trim_code(code)) for code in raw_emoji)):
            return "-".join(self.trim_code(code) for code in raw_emoji)
        if is_emoji(self.emoji(raw_first)):
            return raw_first

        raise ValueError("No codepoint could be obtained from the given input")

    @commands.command(aliases=("tw",))
    async def twemoji(self, ctx: commands.Context, *raw_emoji: str) -> None:
        if len(raw_emoji) == 0:
            await invoke_help_command(ctx)
            return
        try:
            codepoint = self.codepoint_from_input(raw_emoji)
        except (ValueError, AttributeError) as e:
            raise commands.BadArgument(
                "please include a valid emoji or emoji code point."
            )

        await ctx.send(embed=self.build_embed(codepoint))


def setup(bot: Bot) -> None:
    """Load the Twemoji cog."""
    bot.add_cog(Twemoji(bot))

import logging
import re
from typing import Literal

import discord
from discord.ext import commands
from emoji import UNICODE_EMOJI_ENGLISH, is_emoji

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
        """Returns a source file URL for the specified Twemoji, in the corresponding format."""
        return f"{BASE_URLS[format]}{codepoint}.{format}"

    @staticmethod
    def alias_to_name(alias: str) -> str:
        """
        Transform a unicode alias to an emoji name.

        Example usages:
        >>> alias_to_name(":falling_leaf:")
        "Falling leaf"
        >>> alias_to_name(":family_man_girl_boy:")
        "Family man girl boy"
        """
        name = alias[1:-1].replace("_", " ")
        return name.capitalize()

    @staticmethod
    def build_embed(codepoint: str) -> discord.Embed:
        """Returns the main embed for the `twemoji` commmand."""
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
        """
        Returns the emoji corresponding to a given codepoint.

        The return value is an emoji character, such as "🍂". The `codepoint`
        argument can be of any format, since it will be trimmed automatically.
        """
        if code := Twemoji.trim_code(codepoint):
            return chr(int(code, 16))
        return ""

    @staticmethod
    def codepoint(emoji: str) -> str:
        """
        Returns the codepoint of a single emoji.

        `emoji` should be an emoji character, such as "🐍" and "🥰", and
        not a codepoint like "1f1f8". When working with combined emojis,
        such as "🇸🇪" and "👨‍👩‍👦", send the component emojis through the
        method one at a time.
        """
        return hex(ord(emoji))[2:]

    @staticmethod
    def trim_code(codepoint: str) -> str:
        """
        Extract the meaninful information from codepoints, or None, if no codepoint was found.

        Example usages:
        >>> trim_code("U+1f1f8")
        "1f1f8"
        >>> trim_code("\u0001f1f8")
        "1f1f8"
        >>> trim_code("1f466")
        "1f466"
        """
        if code := CODE.search(str(codepoint)):
            return code.group()

    def codepoint_from_input(self, raw_emoji: list[str]) -> str:
        """
        Returns the codepoint corresponding to the passed list, separated by "-".

        The return format matches the format used in URLs for Twemoji source files.

        Example usages:
        >>> codepoint_from_input(["🐍"])
        "1f40d"
        >>> codepoint_from_input(["1f1f8", "1f1ea"])
        "1f1f8-1f1ea"
        >>> codepoint_from_input(["👨‍👧‍👦"])
        "1f468-200d-1f467-200d-1f466"
        """
        raw_emoji = [emoji.lower() for emoji in raw_emoji]
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
        """Sends a preview of a given Twemoji, specified by codepoint or emoji."""
        if len(raw_emoji) == 0:
            await invoke_help_command(ctx)
            return
        try:
            codepoint = self.codepoint_from_input(raw_emoji)
        except (ValueError, AttributeError):
            raise commands.BadArgument(
                "please include a valid emoji or emoji code point."
            )

        await ctx.send(embed=self.build_embed(codepoint))


def setup(bot: Bot) -> None:
    """Load the Twemoji cog."""
    bot.add_cog(Twemoji(bot))

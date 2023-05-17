import logging
import re
from typing import Literal

import discord
from discord.ext import commands
from emoji import EMOJI_DATA, is_emoji

from bot.bot import Bot
from bot.constants import Colours, Roles
from bot.utils.decorators import whitelist_override

log = logging.getLogger(__name__)
BASE_URLS = {
    "png": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/",
    "svg": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/svg/",
}
CODEPOINT_REGEX = re.compile(r"[a-f1-9][a-f0-9]{3,5}$")


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
        name = alias.strip(":").replace("_", " ")
        return name.capitalize()

    @staticmethod
    def build_embed(codepoint: str) -> discord.Embed:
        """Returns the main embed for the `twemoji` commmand."""
        emoji = "".join(Twemoji.emoji(e) or "" for e in codepoint.split("-"))

        embed = discord.Embed(
            title=Twemoji.alias_to_name(EMOJI_DATA[emoji]["en"]),
            description=f"{codepoint.replace('-', ' ')}\n[Download svg]({Twemoji.get_url(codepoint, 'svg')})",
            colour=Colours.twitter_blue,
        )
        embed.set_thumbnail(url=Twemoji.get_url(codepoint, "png"))
        return embed

    @staticmethod
    def emoji(codepoint: str | None) -> str | None:
        """
        Returns the emoji corresponding to a given `codepoint`, or `None` if no emoji was found.

        The return value is an emoji character, such as "🍂". The `codepoint`
        argument can be of any format, since it will be trimmed automatically.
        """
        if code := Twemoji.trim_code(codepoint):
            return chr(int(code, 16))
        return None

    @staticmethod
    def codepoint(emoji: str | None) -> str | None:
        """
        Returns the codepoint, in a trimmed format, of a single emoji.

        `emoji` should be an emoji character, such as "🐍" and "🥰", and
        not a codepoint like "1f1f8". When working with combined emojis,
        such as "🇸🇪" and "👨‍👩‍👦", send the component emojis through the method
        one at a time.
        """
        if emoji is None:
            return None
        return hex(ord(emoji)).removeprefix("0x")

    @staticmethod
    def trim_code(codepoint: str | None) -> str | None:
        """
        Returns the meaningful information from the given `codepoint`.

        If no codepoint is found, `None` is returned.

        Example usages:
        >>> trim_code("U+1f1f8")
        "1f1f8"
        >>> trim_code("\u0001f1f8")
        "1f1f8"
        >>> trim_code("1f466")
        "1f466"
        """
        if code := CODEPOINT_REGEX.search(codepoint or ""):
            return code.group()
        return None

    @staticmethod
    def codepoint_from_input(raw_emoji: tuple[str, ...]) -> str:
        """
        Returns the codepoint corresponding to the passed tuple, separated by "-".

        The return format matches the format used in URLs for Twemoji source files.

        Example usages:
        >>> codepoint_from_input(("🐍",))
        "1f40d"
        >>> codepoint_from_input(("1f1f8", "1f1ea"))
        "1f1f8-1f1ea"
        >>> codepoint_from_input(("👨‍👧‍👦",))
        "1f468-200d-1f467-200d-1f466"
        """
        raw_emoji = [emoji.lower() for emoji in raw_emoji]
        if is_emoji(raw_emoji[0]):
            emojis = (Twemoji.codepoint(emoji) or "" for emoji in raw_emoji[0])
            return "-".join(emojis)

        emoji = "".join(
            Twemoji.emoji(Twemoji.trim_code(code)) or "" for code in raw_emoji
        )
        if is_emoji(emoji):
            return "-".join(Twemoji.codepoint(e) or "" for e in emoji)

        raise ValueError("No codepoint could be obtained from the given input")

    @commands.command(aliases=("tw",))
    @whitelist_override(roles=(Roles.everyone,))
    async def twemoji(self, ctx: commands.Context, *raw_emoji: str) -> None:
        """Sends a preview of a given Twemoji, specified by codepoint or emoji."""
        if len(raw_emoji) == 0:
            await self.bot.invoke_help_command(ctx)
            return
        try:
            codepoint = self.codepoint_from_input(raw_emoji)
        except ValueError:
            raise commands.BadArgument(
                "please include a valid emoji or emoji codepoint."
            )

        await ctx.send(embed=self.build_embed(codepoint))


async def setup(bot: Bot) -> None:
    """Load the Twemoji cog."""
    await bot.add_cog(Twemoji(bot))

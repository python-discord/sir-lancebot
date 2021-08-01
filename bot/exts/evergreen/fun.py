import functools
import json
import logging
import random
from pathlib import Path
from typing import Callable, Iterable, Tuple, Union

from discord import Embed, Message
from discord.ext import commands
from discord.ext.commands import BadArgument, Cog, Context, MessageConverter, clean_content

from bot import utils
from bot.bot import Bot
from bot.constants import Client, Colours, Emojis
from bot.utils import helpers

log = logging.getLogger(__name__)

UWU_WORDS = {
    "fi": "fwi",
    "l": "w",
    "r": "w",
    "some": "sum",
    "th": "d",
    "thing": "fing",
    "tho": "fo",
    "you're": "yuw'we",
    "your": "yur",
    "you": "yuw",
}


def caesar_cipher(text: str, offset: int) -> Iterable[str]:
    """
    Implements a lazy Caesar Cipher algorithm.

    Encrypts a `text` given a specific integer `offset`. The sign
    of the `offset` dictates the direction in which it shifts to,
    with a negative value shifting to the left, and a positive
    value shifting to the right.
    """
    for char in text:
        if not char.isascii() or not char.isalpha() or char.isspace():
            yield char
            continue

        case_start = 65 if char.isupper() else 97
        true_offset = (ord(char) - case_start + offset) % 26

        yield chr(case_start + true_offset)


class Fun(Cog):
    """A collection of general commands for fun."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self._caesar_cipher_embed = json.loads(Path("bot/resources/evergreen/caesar_info.json").read_text("UTF-8"))

    @staticmethod
    def _get_random_die() -> str:
        """Generate a random die emoji, ready to be sent on Discord."""
        die_name = f"dice_{random.randint(1, 6)}"
        return getattr(Emojis, die_name)

    @commands.command()
    async def roll(self, ctx: Context, num_rolls: int = 1) -> None:
        """Outputs a number of random dice emotes (up to 6)."""
        if 1 <= num_rolls <= 6:
            dice = " ".join(self._get_random_die() for _ in range(num_rolls))
            await ctx.send(dice)
        else:
            raise BadArgument(f"`{Client.prefix}roll` only supports between 1 and 6 rolls.")

    @commands.command(name="uwu", aliases=("uwuwize", "uwuify",))
    async def uwu_command(self, ctx: Context, *, text: clean_content(fix_channel_mentions=True)) -> None:
        """Converts a given `text` into it's uwu equivalent."""
        conversion_func = functools.partial(
            utils.replace_many, replacements=UWU_WORDS, ignore_case=True, match_case=True
        )
        text, embed = await Fun._get_text_and_embed(ctx, text)
        # Convert embed if it exists
        if embed is not None:
            embed = Fun._convert_embed(conversion_func, embed)
        converted_text = conversion_func(text)
        converted_text = helpers.suppress_links(converted_text)
        # Don't put >>> if only embed present
        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"
        await ctx.send(content=converted_text, embed=embed)

    @commands.command(name="randomcase", aliases=("rcase", "randomcaps", "rcaps",))
    async def randomcase_command(self, ctx: Context, *, text: clean_content(fix_channel_mentions=True)) -> None:
        """Randomly converts the casing of a given `text`."""
        def conversion_func(text: str) -> str:
            """Randomly converts the casing of a given string."""
            return "".join(
                char.upper() if round(random.random()) else char.lower() for char in text
            )
        text, embed = await Fun._get_text_and_embed(ctx, text)
        # Convert embed if it exists
        if embed is not None:
            embed = Fun._convert_embed(conversion_func, embed)
        converted_text = conversion_func(text)
        converted_text = helpers.suppress_links(converted_text)
        # Don't put >>> if only embed present
        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"
        await ctx.send(content=converted_text, embed=embed)

    @commands.group(name="caesarcipher", aliases=("caesar", "cc",))
    async def caesarcipher_group(self, ctx: Context) -> None:
        """
        Translates a message using the Caesar Cipher.

        See `decrypt`, `encrypt`, and `info` subcommands.
        """
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command("help"), "caesarcipher")

    @caesarcipher_group.command(name="info")
    async def caesarcipher_info(self, ctx: Context) -> None:
        """Information about the Caesar Cipher."""
        embed = Embed.from_dict(self._caesar_cipher_embed)
        embed.colour = Colours.dark_green

        await ctx.send(embed=embed)

    @staticmethod
    async def _caesar_cipher(ctx: Context, offset: int, msg: str, left_shift: bool = False) -> None:
        """
        Given a positive integer `offset`, translates and sends the given `msg`.

        Performs a right shift by default unless `left_shift` is specified as `True`.

        Also accepts a valid Discord Message ID or link.
        """
        if offset < 0:
            await ctx.send(":no_entry: Cannot use a negative offset.")
            return

        if left_shift:
            offset = -offset

        def conversion_func(text: str) -> str:
            """Encrypts the given string using the Caesar Cipher."""
            return "".join(caesar_cipher(text, offset))

        text, embed = await Fun._get_text_and_embed(ctx, msg)

        if embed is not None:
            embed = Fun._convert_embed(conversion_func, embed)

        converted_text = conversion_func(text)

        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"

        await ctx.send(content=converted_text, embed=embed)

    @caesarcipher_group.command(name="encrypt", aliases=("rightshift", "rshift", "enc",))
    async def caesarcipher_encrypt(self, ctx: Context, offset: int, *, msg: str) -> None:
        """
        Given a positive integer `offset`, encrypt the given `msg`.

        Performs a right shift of the letters in the message.

        Also accepts a valid Discord Message ID or link.
        """
        await self._caesar_cipher(ctx, offset, msg, left_shift=False)

    @caesarcipher_group.command(name="decrypt", aliases=("leftshift", "lshift", "dec",))
    async def caesarcipher_decrypt(self, ctx: Context, offset: int, *, msg: str) -> None:
        """
        Given a positive integer `offset`, decrypt the given `msg`.

        Performs a left shift of the letters in the message.

        Also accepts a valid Discord Message ID or link.
        """
        await self._caesar_cipher(ctx, offset, msg, left_shift=True)

    @staticmethod
    async def _get_text_and_embed(ctx: Context, text: str) -> Tuple[str, Union[Embed, None]]:
        """
        Attempts to extract the text and embed from a possible link to a discord Message.

        Does not retrieve the text and embed from the Message if it is in a channel the user does
        not have read permissions in.

        Returns a tuple of:
            str: If `text` is a valid discord Message, the contents of the message, else `text`.
            Union[Embed, None]: The embed if found in the valid Message, else None
        """
        embed = None

        msg = await Fun._get_discord_message(ctx, text)
        # Ensure the user has read permissions for the channel the message is in
        if isinstance(msg, Message) and ctx.author.permissions_in(msg.channel).read_messages:
            text = msg.clean_content
            # Take first embed because we can't send multiple embeds
            if msg.embeds:
                embed = msg.embeds[0]

        return (text, embed)

    @staticmethod
    async def _get_discord_message(ctx: Context, text: str) -> Union[Message, str]:
        """
        Attempts to convert a given `text` to a discord Message object and return it.

        Conversion will succeed if given a discord Message ID or link.
        Returns `text` if the conversion fails.
        """
        try:
            text = await MessageConverter().convert(ctx, text)
        except commands.BadArgument:
            log.debug(f"Input '{text:.20}...' is not a valid Discord Message")
        return text

    @staticmethod
    def _convert_embed(func: Callable[[str, ], str], embed: Embed) -> Embed:
        """
        Converts the text in an embed using a given conversion function, then return the embed.

        Only modifies the following fields: title, description, footer, fields
        """
        embed_dict = embed.to_dict()

        embed_dict["title"] = func(embed_dict.get("title", ""))
        embed_dict["description"] = func(embed_dict.get("description", ""))

        if "footer" in embed_dict:
            embed_dict["footer"]["text"] = func(embed_dict["footer"].get("text", ""))

        if "fields" in embed_dict:
            for field in embed_dict["fields"]:
                field["name"] = func(field.get("name", ""))
                field["value"] = func(field.get("value", ""))

        return Embed.from_dict(embed_dict)


def setup(bot: Bot) -> None:
    """Load the Fun cog."""
    bot.add_cog(Fun(bot))

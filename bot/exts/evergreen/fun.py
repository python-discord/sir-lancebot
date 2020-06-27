import functools
import json
import logging
import random
from pathlib import Path
from typing import Callable, Tuple, Union

from discord import Embed, Message
from discord.ext import commands
from discord.ext.commands import Bot, Cog, Context, MessageConverter

from bot import utils
from bot.constants import Colours, Emojis

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


class Fun(Cog):
    """A collection of general commands for fun."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        with Path("bot/resources/evergreen/caesar_info.json").open("r") as f:
            self._caesar_cipher_embed = json.load(f)

    @commands.command()
    async def roll(self, ctx: Context, num_rolls: int = 1) -> None:
        """Outputs a number of random dice emotes (up to 6)."""
        output = ""
        if num_rolls > 6:
            num_rolls = 6
        elif num_rolls < 1:
            output = ":no_entry: You must roll at least once."
        for _ in range(num_rolls):
            terning = f"terning{random.randint(1, 6)}"
            output += getattr(Emojis, terning, '')
        await ctx.send(output)

    @commands.command(name="uwu", aliases=("uwuwize", "uwuify",))
    async def uwu_command(self, ctx: Context, *, text: str) -> None:
        """
        Converts a given `text` into it's uwu equivalent.

        Also accepts a valid discord Message ID or link.
        """
        conversion_func = functools.partial(
            utils.replace_many, replacements=UWU_WORDS, ignore_case=True, match_case=True
        )
        text, embed = await Fun._get_text_and_embed(ctx, text)
        # Convert embed if it exists
        if embed is not None:
            embed = Fun._convert_embed(conversion_func, embed)
        converted_text = conversion_func(text)
        # Don't put >>> if only embed present
        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"
        await ctx.send(content=converted_text, embed=embed)

    @commands.command(name="randomcase", aliases=("rcase", "randomcaps", "rcaps",))
    async def randomcase_command(self, ctx: Context, *, text: str) -> None:
        """
        Randomly converts the casing of a given `text`.

        Also accepts a valid discord Message ID or link.
        """
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
        # Don't put >>> if only embed present
        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"
        await ctx.send(content=converted_text, embed=embed)

    @commands.group(name="caesarcipher", aliases=("caesar",))
    async def caesarcipher_group(self, ctx: Context) -> None:
        """
        Translates a message using the Caesar Cipher.

        See `decrpyt`, `encrypt`, and `info` subcommands.
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
    async def _caesar_cipher(ctx: Context, offset: int, msg: Union[Message, str]) -> None:
        """
        Given an integer `offset`, translates and sends the given `text`.

        A positive `offset` will cause the letters to shift right, while
        a negative `offset` will cause the letters to shift left.

        Also accepts a valid Discord Message ID or link.
        """
        def caesar_func(text: str) -> str:
            """Implements a lazy Caesar Cipher algorithm."""
            for char in text:
                if not char.isascii() or not char.isalpha() or char.isspace():
                    yield char
                    continue
                case_start = 65 if char.isupper() else 97
                yield chr((ord(char) - case_start + offset) % 26 + case_start)

        def conversion_func(text: str) -> str:
            """Encrypts the given string using the Caesar Cipher."""
            return "".join(caesar_func(text))

        is_message = isinstance(msg, Message)

        text = msg.content if is_message else msg
        embed = msg.embeds[0] if is_message and msg.embeds else None

        if embed is not None:
            embed = Fun._convert_embed(conversion_func, embed)

        converted_text = conversion_func(text)

        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"

        await ctx.send(content=converted_text, embed=embed)

    @caesarcipher_group.command(name="encrypt", aliases=("rightshift", "rshift"))
    async def caesarcipher_encrypt(self, ctx: Context, offset: int, *, msg: Union[Message, str]) -> None:
        """
        Given a positive integer `offset`, encrypt the given `text`.

        Performs a right shift of the letters in the message.

        Also accepts a valid Discord Message ID or link.
        """
        if offset < 0:
            await ctx.send(":no_entry: Cannot use a negative offset.")
        else:
            await self._caesar_cipher(ctx, offset, msg)

    @caesarcipher_group.command(name="decrypt", aliases=("leftshift", "lshift"))
    async def caesarcipher_decrypt(self, ctx: Context, offset: int, *, msg: Union[Message, str]) -> None:
        """
        Given a positive integer `offset`, decrypt the given `text`.

        Performs a left shift of the letters in the message.

        Also accepts a valid Discord Message ID or link.
        """
        if offset < 0:
            await ctx.send(":no_entry: Cannot use a negative offset.")
        else:
            await self._caesar_cipher(ctx, -offset, msg)

    @staticmethod
    async def _get_text_and_embed(ctx: Context, text: str) -> Tuple[str, Union[Embed, None]]:
        """
        Attempts to extract the text and embed from a possible link to a discord Message.

        Returns a tuple of:
            str: If `text` is a valid discord Message, the contents of the message, else `text`.
            Union[Embed, None]: The embed if found in the valid Message, else None
        """
        embed = None
        message = await Fun._get_discord_message(ctx, text)
        if isinstance(message, Message):
            text = message.content
            # Take first embed because we can't send multiple embeds
            if message.embeds:
                embed = message.embeds[0]
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


def setup(bot: commands.Bot) -> None:
    """Fun Cog load."""
    bot.add_cog(Fun(bot))

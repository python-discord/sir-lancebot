import json
import random
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

import pyjokes
from discord import Embed
from discord.ext import commands
from discord.ext.commands import BadArgument, Cog, Context
from pydis_core.utils.commands import clean_text_or_reply
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import Client, Colours, Emojis
from bot.utils import helpers, messages

log = get_logger(__name__)


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

    def __init__(self, bot: Bot):
        self.bot = bot
        self._caesar_cipher_embed = json.loads(Path("bot/resources/fun/caesar_info.json").read_text("UTF-8"))

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

    @commands.command(name="randomcase", aliases=("rcase", "randomcaps", "rcaps",))
    async def randomcase_command(self, ctx: Context, *, text: str | None) -> None:
        """Randomly converts the casing of a given `text`, or the replied message."""
        def conversion_func(text: str) -> str:
            """Randomly converts the casing of a given string."""
            return "".join(
                char.upper() if round(random.random()) else char.lower() for char in text
            )
        text = await clean_text_or_reply(ctx, text)
        text, embed = await messages.get_text_and_embed(ctx, text)
        # Convert embed if it exists
        if embed is not None:
            embed = messages.convert_embed(conversion_func, embed)
        converted_text = conversion_func(text)
        converted_text = helpers.suppress_links(converted_text)
        # Don't put >>> if only embed present
        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"
        await ctx.send(content=converted_text, embed=embed)
        
    @commands.command(name="snakecase", aliases=("scase",))
    async def snakecase_command(self, ctx: Context, *, text: str | None) -> None:
        """Attempts to convert the provided string to snake_case."""
        text = helpers.neutralise_string(text)
        def conversion_func(text: str) -> str:
            """Converts the provided string to snake_case."""
            return "_".join(
                text.split()
            )
        text = await clean_text_or_reply(ctx, text)
        text, embed = await messages.get_text_and_embed(ctx, text)
        # Convert embed if it exists
        if embed is not None:
            embed = messages.convert_embed(conversion_func, embed)
        converted_text = conversion_func(text)
        converted_text = helpers.suppress_links(converted_text)
        # Don't put >>> if only embed present
        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"
        await ctx.send(content=converted_text, embed=embed)

    @commands.command(name="pascalcase", aliases=("pcase", "pascal",))
    async def pascalcase_command(self, ctx: Context, *, text: str | None) -> None:
        """Attempts to convert the provided string to pascalCase."""
        text = helpers.neutralise_string(text)
        def conversion_func(text: str) -> str:
            """Converts the provided string to pascalCase."""
            return "".join(
                word[0].upper()+word[1:] if i != 0 else word for i, word in enumerate(text.split())
            )
        text = await clean_text_or_reply(ctx, text)
        text, embed = await messages.get_text_and_embed(ctx, text)
        # Convert embed if it exists
        if embed is not None:
            embed = messages.convert_embed(conversion_func, embed)
        converted_text = conversion_func(text)
        converted_text = helpers.suppress_links(converted_text)
        # Don't put >>> if only embed present
        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"
        await ctx.send(content=converted_text, embed=embed)

    @commands.command(name="screamingsnakecase", aliases=("screamsnake", "ssnake","screamingsnake",))
    async def screamingsnakecase_command(self, ctx: Context, *, text: str | None) -> None:
        """Attempts to convert the provided string to SCREAMING_SNAKE_CASE."""
        text = helpers.neutralise_string(text)
        def conversion_func(text: str) -> str:
            """Converts the provided string to SCREAMING_SNAKE_CASE."""
            return "_".join(
                word.upper() for word in text.split()
            )
        text = await clean_text_or_reply(ctx, text)
        text, embed = await messages.get_text_and_embed(ctx, text)
        # Convert embed if it exists
        if embed is not None:
            embed = messages.convert_embed(conversion_func, embed)
        converted_text = conversion_func(text)
        converted_text = helpers.suppress_links(converted_text)
        # Don't put >>> if only embed present
        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"
        await ctx.send(content=converted_text, embed=embed)

    @commands.command(name="camelcase", aliases=("ccase", "camel",))
    async def camelcase_command(self, ctx: Context, *, text: str | None) -> None:
        """Attempts to convert the provided string to CamelCase."""
        text = helpers.neutralise_string(text)
        def conversion_func(text: str) -> str:
            """Converts the provided string to CamelCase."""
            return "".join(
                word[0].upper()+word[1:] for word in text.split()
            )
        text = await clean_text_or_reply(ctx, text)
        text, embed = await messages.get_text_and_embed(ctx, text)
        # Convert embed if it exists
        if embed is not None:
            embed = messages.convert_embed(conversion_func, embed)
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

        text, embed = await messages.get_text_and_embed(ctx, msg)

        if embed is not None:
            embed = messages.convert_embed(conversion_func, embed)

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

    @commands.command()
    async def joke(self, ctx: commands.Context, category: Literal["neutral", "chuck", "all"] = "all") -> None:
        """Retrieves a joke of the specified `category` from the pyjokes api."""
        joke = pyjokes.get_joke(category=category)
        await ctx.send(joke)


async def setup(bot: Bot) -> None:
    """Load the Fun cog."""
    await bot.add_cog(Fun(bot))

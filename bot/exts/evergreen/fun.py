import functools
import logging
import random
from typing import Callable, Tuple, Union

from discord import Embed, Message
from discord.ext import commands
from discord.ext.commands import Bot, Cog, Context, MessageConverter, clean_content

from bot import utils
from bot.constants import Emojis

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

    @commands.command()
    async def roll(self, ctx: Context, num_rolls: int = 1) -> None:
        """Outputs a number of random dice emotes (up to 6)."""
        output = ""
        if num_rolls > 6:
            num_rolls = 6
        elif num_rolls < 1:
            output = ":no_entry: You must roll at least once."
        for _ in range(num_rolls):
            dice = f"dice_{random.randint(1, 6)}"
            output += getattr(Emojis, dice, '')
        await ctx.send(output)

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
        # Don't put >>> if only embed present
        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"
        await ctx.send(content=converted_text, embed=embed)

    @commands.command(name="randomcase", aliases=("rcase", "randomcaps", "rcaps",))
    async def randomcase_command(self, ctx: Context, *, text: str) -> None:
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
        # Don't put >>> if only embed present
        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"
        await ctx.send(content=converted_text, embed=embed)

    @staticmethod
    async def _get_text_and_embed(ctx: Context, text: str) -> Tuple[str, Union[Embed, None]]:
        """
        Attempts to extract the text and embed from a possible link to a discord Message.

        Returns a tuple of:
            str: If `text` is a valid discord Message, the contents of the message, else `text`.
            Union[Embed, None]: The embed if found in the valid Message, else None
        """
        embed = None

        # message = await Fun._get_discord_message(ctx, text)
        # if isinstance(message, Message):
        #     text = message.content
        #     # Take first embed because we can't send multiple embeds
        #     if message.embeds:
        #         embed = message.embeds[0]

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

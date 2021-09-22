import random
import re
from functools import partial
from typing import Callable

from discord.ext import commands
from discord.ext.commands import Cog, Context, clean_content

from bot.bot import Bot
from bot.exts.fun.fun import Fun
from bot.utils import helpers


WORD_REPLACE_HASH = {
    "small": "smol",
    "cute": "kawaii~",
    "fluff": "floof",
    "love": "luv",
    "stupid": "baka",
    "idiot": "baka",
    "what": "nani",
    "meow": "nya~",
    "roar": "rawrr~",
}

EMOJI_LUT = [
    "rawr x3",
    "OwO",
    "UwU",
    "o.O",
    "-.-",
    ">w<",
    "σωσ",
    "òωó",
    "ʘwʘ",
    ":3",
    "XD",
    "nyaa~~",
    "mya",
    ">_<",
    "rawr",
    "uwu",
    "^^",
    "^^;;",
]

word_replace_regex = re.compile(r"(?<![w])[lr](?![w])")

punctuation_regex = re.compile(r"[.!?\r\n\t]")

stutter_regex = re.compile(r"(\s)([a-zA-Z])")
stutter_substitute = "\\g<1>\\g<2>-\\g<2>"

nya_regex = re.compile(r"n([aeou])([^aeiou])")
nya_substitute = "ny\\g<1>\\g<2>"


def _word_replace(input_string: str) -> str:
    """Replaces words that are keys in the word replacement hash to the values specified."""
    for word in WORD_REPLACE_HASH:
        input_string = input_string.replace(word, WORD_REPLACE_HASH[word])
    return input_string


def _char_replace(input_string: str) -> str:
    """Replaces characters with 'w'."""
    return word_replace_regex.sub("w", input_string)


def _stutter(strength: float, input_string: str) -> str:
    """Adds stuttering to a string."""
    return stutter_regex.sub(partial(_stutter_replace, strength=strength), input_string, 0)


def _stutter_replace(match: Callable, strength: float = 0.0) -> str:
    """Replaces a single character with a stuttered character."""
    match_string = match.string[slice(*match.span())]
    if random.random() < strength:
        char = match_string[-1]
        return f"{match_string}-{char}"
    return match_string


def _nyaify(input_string: str) -> str:
    """Nyaifies a string."""
    return nya_regex.sub(nya_substitute, input_string, 0)


def _emoji(strength: float, input_string: str) -> str:
    """Replaces some punctuation with emoticons."""
    return punctuation_regex.sub(partial(_emoji_replace, strength=strength), input_string, 0)


def _emoji_replace(match: Callable, strength: float = 0.0) -> str:
    """Replaces a punctuation character with an emoticon."""
    match_string = match.string[slice(*match.span())]
    if random.random() < strength:
        return f" {EMOJI_LUT[random.randint(0, len(EMOJI_LUT) - 1)]} "
    return match_string


def _uwuify(input_string: str, *, stutter_strength: float = 0.2, emoji_strength: float = 0.1) -> str:
    """Takes a string and returns an uwuified version of it."""
    input_string = input_string.lower()
    input_string = _word_replace(input_string)
    input_string = _nyaify(input_string)
    input_string = _char_replace(input_string)
    input_string = _stutter(stutter_strength, input_string)
    input_string = _emoji(emoji_strength, input_string)
    return input_string


class Uwu(Cog):
    """Cog for the uwu command."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="uwu", aliases=("uwuwize", "uwuify",))
    async def uwu_command(self, ctx: Context, *, text: clean_content(fix_channel_mentions=True)) -> None:
        """
        Echoes an uwuified version of a message.

        Example:
        '.uwu Hello, my name is John' returns something like
        'hewwo, m-my name is j-john nyaa~'.
        """
        text, embed = await Fun._get_text_and_embed(ctx, text)

        # Grabs the text from the embed for uwuification.
        if embed is not None:
            embed = Fun._convert_embed(_uwuify, embed)
        converted_text = _uwuify(text)
        converted_text = helpers.suppress_links(converted_text)

        # Adds the text harvested from an embed to be put into another quote block.
        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"
        await ctx.send(content=converted_text, embed=embed)


def setup(bot: Bot) -> None:
    """Load the uwu cog."""
    bot.add_cog(Uwu(bot))

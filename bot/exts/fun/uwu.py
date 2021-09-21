import random
import re
from functools import partial
from typing import Callable

from discord.ext import commands
from discord.ext.commands import Cog, Context, clean_content

from bot.bot import Bot
from bot.exts.fun.fun import Fun
from bot.utils import helpers


# Wepwacement
WEPWACE_HASH = {
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
    "(⑅˘꒳˘)",
    "(ꈍᴗꈍ)",
    "(˘ω˘)",
    "(U ᵕ U❁)",
    "σωσ",
    "òωó",
    "(///ˬ///✿)",
    "(U ﹏ U)",
    "( ͡o ω ͡o )",
    "ʘwʘ",
    ":3",
    ":3",  # important enough to have twice
    "XD",
    "nyaa~~",
    "mya",
    ">_<",
    "😳",
    "🥺",
    "😳😳😳",
    "rawr",
    "uwu",
    "^^",
    "^^;;",
    "(ˆ ﻌ ˆ)♡",
    "^•ﻌ•^",
    "/(^•ω•^)",
    "(✿oωo)",
]

wepwace_regex = re.compile(r"(?<![w])[lr](?![w])")


def _word_replace(input_string: str) -> str:
    for word in WEPWACE_HASH:
        input_string = input_string.replace(word, WEPWACE_HASH[word])

    return input_string


def _char_replace(input_string: str) -> str:
    return wepwace_regex.sub("w", input_string)


# Stuttering
stutter_regex = re.compile(r"(\s)([a-zA-Z])")
stutter_subst = "\\g<1>\\g<2>-\\g<2>"


def _stutter(strength: float, input_string: str) -> str:
    return stutter_regex.sub(partial(_stutter_replace, strength=strength), input_string, 0)


def _stutter_replace(match: Callable, strength: float = 0.0) -> str:
    match_string = match.string[slice(*match.span())]
    if random.random() < strength:
        char = match_string[-1]
        return f"{match_string}-{char}"
    return match_string


# Nyaification
nya_regex = re.compile(r"n([aeou])([^aeiou])")
nya_subst = "ny\\g<1>\\g<2>"


def _nyaify(input_string: str) -> str:
    return nya_regex.sub(nya_subst, input_string, 0)


# Emoji
punctuation_regex = re.compile(r"\s+")


def _emoji(strength: float, input_string: str) -> str:
    return punctuation_regex.sub(partial(_emoji_replace, strength=strength), input_string, 0)


def _emoji_replace(match: Callable, strength: float = 0.0) -> str:
    match_string = match.string[slice(*match.span())]
    if random.random() < strength:
        return f" {EMOJI_LUT[random.randint(0, len(EMOJI_LUT) - 1)]} "

    return match_string


# Main

def _uwuify(input_string: str, *, stutter_strength: float = 0.2, emoji_strength: float = 0.2) -> str:
    input_string = input_string.lower()
    input_string = _word_replace(input_string)
    input_string = _nyaify(input_string)
    input_string = _char_replace(input_string)
    input_string = _stutter(stutter_strength, input_string)
    input_string = _emoji(emoji_strength, input_string)
    return input_string


class Uwu(Cog):
    """Cog for uwuification."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="uwu", aliases=("uwuwize", "uwuify",))
    async def uwu_command(self, ctx: Context, *, text: clean_content(fix_channel_mentions=True)) -> None:
        """Converts a given `text` into it's uwu equivalent."""
        text, embed = await Fun._get_text_and_embed(ctx, text)
        # Convert embed if it exists
        if embed is not None:
            embed = Fun._convert_embed(_uwuify, embed)
        converted_text = _uwuify(text)
        converted_text = helpers.suppress_links(converted_text)
        # Don't put >>> if only embed present
        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"
        await ctx.send(content=converted_text, embed=embed)


def setup(bot: Bot) -> None:
    """Load the uwu cog."""
    bot.add_cog(Uwu(bot))

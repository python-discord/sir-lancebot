#!/usr/bin/env python3

import re
import random
import re
from functools import partial

from bot.utils import helpers

from bot.bot import Bot

from bot.exts.fun.fun import Fun

from discord import Message
from discord.ext import commands
from discord.ext.commands import Cog, Context, clean_content

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
    ":3", # important enough to have twice
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

def word_replace(input_string: str) -> str:
    for word in WEPWACE_HASH:
        input_string = input_string.replace(word, WEPWACE_HASH[word])

    return input_string

def char_replace(input_string: str) -> str:
    return wepwace_regex.sub("w", input_string)

# Stuttering
stutter_regex = re.compile(r"(\s)([a-zA-Z])")
stutter_subst = "\\g<1>\\g<2>-\\g<2>"

def stutter(strength: float, input_string: str):
        return stutter_regex.sub(partial(stutter_replace, strength=strength), input_string, 0)

def stutter_replace(match, strength = 0.0):
    match_string = match.string[slice(*match.span())]
    if random.random() < strength:
        char = match_string[-1]
        return f"{match_string}-{char}"
    return match_string

# Nyaification
nya_regex = re.compile(r"n([aeou])([^aeiou])")
nya_subst = "ny\\g<1>\\g<2>"

def nyaify(input_string):
    return nya_regex.sub(nya_subst, input_string, 0)

# Emoji
punctuation_regex = re.compile(r"\s+")

def emoji(strength: float, input_string: str):
        return punctuation_regex.sub(partial(emoji_replace, strength=strength), input_string, 0)


def emoji_replace(match, strength = 0.0):
    match_string = match.string[slice(*match.span())]
    if random.random() < strength:
        return f" {EMOJI_LUT[random.randint(0, len(EMOJI_LUT) - 1)]} "

    return match_string

# Main

def uwuify(input_string: str, *, stutter_strength: float = 0.2, emoji_strength: float = 0.2) -> str:
        input_string = input_string.lower()
        input_string = word_replace(input_string)
        input_string = nyaify(input_string)
        input_string = char_replace(input_string)
        input_string = stutter(stutter_strength, input_string)
        input_string = emoji(emoji_strength, input_string)
        return input_string

class Uwu(Cog):
    """
    Cog for uwuification.
    """
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="uwu", aliases=("uwuwize", "uwuify",))
    async def uwu_command(self, ctx: Context, *, text: clean_content(fix_channel_mentions=True)) -> None:
        """Converts a given `text` into it's uwu equivalent."""
        text, embed = await Fun._get_text_and_embed(ctx, text)
        # Convert embed if it exists
        if embed is not None:
            embed = Fun._convert_embed(uwuify, embed)
        converted_text = uwuify(text)
        converted_text = helpers.suppress_links(converted_text)
        # Don't put >>> if only embed present
        if converted_text:
            converted_text = f">>> {converted_text.lstrip('> ')}"
        await ctx.send(content=converted_text, embed=embed)

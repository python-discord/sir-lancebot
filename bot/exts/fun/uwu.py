import random
import re
from functools import partial

from discord.ext import commands
from discord.ext.commands import Cog, Context, clean_content

from bot.bot import Bot
from bot.exts.fun.fun import Fun
from bot.utils import helpers

WORD_REPLACE = {
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

EMOJIS = [
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

REGEX_WORD_REPLACE = re.compile(r"(?<![w])[lr](?![w])")

REGEX_PUNCTUATION = re.compile(r"[.!?\r\n\t]")

REGEX_STUTTER = re.compile(r"(\s)([a-zA-Z])")
SUBSTITUTE_STUTTER = r"\g<1>\g<2>-\g<2>"

REGEX_NYA = re.compile(r"n([aeou][^aeiou])")
SUBSTITUTE_NYA = r"ny\1"


class Uwu(Cog):
    """Cog for the uwu command."""

    def __init__(self, bot: Bot):
        self.bot = bot

    def _word_replace(self, input_string: str) -> str:
        """Replaces words that are keys in the word replacement hash to the values specified."""
        for word, replacement in WORD_REPLACE.items():
            input_string = input_string.replace(word, replacement)
        return input_string

    def _char_replace(self, input_string: str) -> str:
        """Replace certain characters with 'w'."""
        return REGEX_WORD_REPLACE.sub("w", input_string)

    def _stutter(self, strength: float, input_string: str) -> str:
        """Adds stuttering to a string."""
        return REGEX_STUTTER.sub(partial(self._stutter_replace, strength=strength), input_string, 0)

    def _stutter_replace(self, match: re.Match, strength: float = 0.0) -> str:
        """Replaces a single character with a stuttered character."""
        match_string = match.group()
        if random.random() < strength:
            return f"{match_string}-{match_string[-1]}"  # Stutter the last character
        return match_string

    def _nyaify(self, input_string: str) -> str:
        """Nyaifies a string by adding a 'y' between an 'n' and a vowel."""
        return REGEX_NYA.sub(SUBSTITUTE_NYA, input_string, 0)

    def _emoji(self, strength: float, input_string: str) -> str:
        """Replaces some punctuation with emoticons."""
        return REGEX_PUNCTUATION.sub(partial(self._emoji_replace, strength=strength), input_string, 0)

    def _emoji_replace(self, match: re.Match, strength: float = 0.0) -> str:
        """Replaces a punctuation character with an emoticon."""
        match_string = match.group()
        if random.random() < strength:
            return f" {random.choice(EMOJIS)} "
        return match_string

    def _uwuify(self, input_string: str, *, stutter_strength: float = 0.2, emoji_strength: float = 0.1) -> str:
        """Takes a string and returns an uwuified version of it."""
        input_string = input_string.lower()
        input_string = self._word_replace(input_string)
        input_string = self._nyaify(input_string)
        input_string = self._char_replace(input_string)
        input_string = self._stutter(stutter_strength, input_string)
        input_string = self._emoji(emoji_strength, input_string)
        return input_string

    @commands.command(name="uwu", aliases=("uwuwize", "uwuify",))
    async def uwu_command(self, ctx: Context, *, text: clean_content(fix_channel_mentions=True)) -> None:
        """
        Echo an uwuified version the passed text.

        Example:
        '.uwu Hello, my name is John' returns something like
        'hewwo, m-my name is j-john nyaa~'.
        """
        if (fun_cog := ctx.bot.get_cog("Fun")):
            text, embed = await fun_cog._get_text_and_embed(ctx, text)

           # Grabs the text from the embed for uwuification.
           if embed is not None:
               embed = fun_cog._convert_embed(self._uwuify, embed)
        else:
            embed = None
        converted_text = self._uwuify(text)
        converted_text = helpers.suppress_links(converted_text)

        # Adds the text harvested from an embed to be put into another quote block.
        converted_text = f">>> {converted_text.lstrip('> ')}"
        await ctx.send(content=converted_text, embed=embed)


def setup(bot: Bot) -> None:
    """Load the uwu cog."""
    bot.add_cog(Uwu(bot))

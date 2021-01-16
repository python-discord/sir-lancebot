import logging
import random
import string
from asyncio import TimeoutError
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

import async_timeout
import markovify
from discord import Embed
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)


class RhymeNotFound(Exception):
    """Raised when a word has no other rhymes."""

    pass


class RhymingSentenceNotFound(Exception):
    """Raised when a rhyming sentence could not be found."""

    pass


class MarkovPoemGenerator(commands.Cog):
    """A cog that provides a poem by taking the markov of a corpus."""

    SOURCES: List[str] = [
        "shakespeare_corpus.txt"
    ]

    templates: Dict[str, str] = {
        "shakespearean-sonnet": "abab/cdcd/efef/gg"
    }

    rhymeless_words: Set[str] = set()
    rhymeless_then_instant_fail: Dict[str, bool] = defaultdict(lambda: False)
    curr_unit = None

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        for source_file in self.SOURCES:
            with Path(f"bot/resources/valentines/{source_file}").open() as f:
                full_corpus = f.read().splitlines()

        # Create a markov model
        self.model = markovify.Text(full_corpus, state_size=1)

        # For caching rhymes
        self.rhymes: Dict[str, Set[str]] = {}

    @staticmethod
    def _get_last_word(sentence: str) -> str:
        """Returns the last word of a sentence string."""
        if isinstance(sentence, str) is False:
            # Likely to be caused by `make_short_sentence` running out
            # and feeding it None
            raise TypeError(f"Argument is a {type(sentence)} instead of a str.")
        return sentence.strip(string.punctuation).split()[-1]

    async def _get_rhyming_words(self, word: str) -> List[str]:
        """Returns a list of words that rhyme with `word`."""
        word = word.replace("'", "e")  # Sometimes e is replaced with '

        # Caches results to reduce client sessions
        if word in self.rhymes:
            return self.rhymes[word]

        rhyme_set = set()

        # Exact rhymes
        async with self.bot.http_session.get(
            "https://api.datamuse.com/words?rel_rhy=" + word,
            timeout=10
        ) as response:
            exact_rhyme_set = set(
                data["word"] for data in await response.json()
            )
            rhyme_set |= exact_rhyme_set

        # Near rhymes, with their nearness measured by its score
        async with self.bot.http_session.get(
            "https://api.datamuse.com/words?rel_rhy=" + word,
            timeout=10
        ) as response:
            close_rhyme_set = set(
                data["word"] for data in await response.json()
                if data.get("score", 0) > 2000
            )
            rhyme_set |= close_rhyme_set

        if len(rhyme_set) == 0:
            logging.info(f"No rhymes were found for the word: {word}")
            self.rhymeless_words.add(word)
            if self.rhymeless_then_instant_fail[self.curr_unit]:
                raise RhymeNotFound

        self.rhymes[word] = rhyme_set
        return rhyme_set

    async def _get_rhyming_line(
        self,
        word: str = None,
        word_rhymes: List[str] = None
    ) -> str:
        """
        Returns a sentence string that rhymes with `word` in `word_rhymes`.

        The function will continue to iterate through sentences
        until it finds one that rhymes with `word` or in `word_rhymes`.

        Note that if both `word` and `word_rhymes` are not None,
        then `word_rhymes` will take priority.
        """
        if word_rhymes is None and word is not None:
            word_rhymes = await self._get_rhyming_words(word)
        elif word_rhymes is None and word is None:
            raise TypeError("Both arguments cannot be NoneType.")

        curr = 0
        line = self.model.make_short_sentence(random.randint(50, 120))
        while self._get_last_word(line) not in word_rhymes:
            if curr >= 80000:  # Limiter
                raise RhymingSentenceNotFound

            line = self.model.make_short_sentence(
                random.randint(50, 120)
            )
            curr += 1

        return line

    @commands.command()
    async def poem(self, ctx: commands.Context, structure: str) -> None:
        """
        Gives the user a love poem.

        The blackslash character creates a new stanza.
        """
        if structure in self.templates:
            structure = self.templates[structure]

        # Checks if all characters
        for char in set(structure):
            if structure.count(char) >= 2:
                self.rhymeless_then_instant_fail[char] = True

        try:
            async with async_timeout.timeout(20), ctx.typing():
                acc_lines = []
                stanzas = []
                rhyme_track = {}  # Maps units to their rhyme sets

                for unit in structure:
                    self.curr_unit = unit

                    # Create new stanza
                    if unit == "/":
                        new_stanza = "\n".join(acc_lines)
                        stanzas.append(new_stanza)
                        acc_lines = []
                        continue

                    if unit not in rhyme_track:
                        new_line = self.model.make_short_sentence(
                            random.randint(50, 120)
                        )
                        acc_lines.append(new_line)

                        last_word = self._get_last_word(new_line)
                        if last_word in self.rhymeless_words:
                            return await ctx.send("Rhymeless word.")

                        try:
                            rhyme_track[unit] = await self._get_rhyming_words(
                                last_word
                            )
                        except RhymeNotFound:
                            return await ctx.send("Rhyme impossible, instant.")
                    else:
                        try:
                            new_line = await self._get_rhyming_line(
                                word_rhymes=rhyme_track[unit]
                            )
                        except RhymingSentenceNotFound:
                            return await ctx.send("Sentence failed.")

                        acc_lines.append(new_line)

                stanzas.append("\n".join(acc_lines))  # Append final stanza
                # await ctx.send("\n\n".join(stanzas))

                poem_embed = Embed(
                    title="Shakespeare Markov Poem",
                    color=Colours.pink,
                    description="\n\n".join(stanzas)
                )
                await ctx.send(embed=poem_embed)
        except TimeoutError:
            logging.warning("Poem generator timed out.")
            await ctx.send("Unlucky, try again!")


def setup(bot: commands.Bot) -> None:
    """Poem generator cog load."""
    bot.add_cog(MarkovPoemGenerator(bot))

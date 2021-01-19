import functools
import logging
import random
import string
from asyncio import TimeoutError
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Callable, Dict, List, Optional, Set, Tuple, Type

import async_timeout
import markovify
from discord import Embed
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)


class RhymingSentenceNotFound(commands.CommandError):
    """Raised when a rhyming sentence could not be found."""

    pass


class Cache:
    """A context manager to facilitate storage of word to rhyme sets."""

    cache: Dict[str, Set[str]] = {}

    def __init__(self, word: str, is_instant_fail: bool):
        self.word = word
        self.is_instant_fail = is_instant_fail

    def __enter__(self):
        self.word = self.word.replace("'", "e")  # Sometimes ' replaces e
        return (self.cache, self.word)

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType]
    ):
        if len(self.cache[self.word]) == 0:
            logging.info(f"No rhymes were found for the word: {self.word}")


def memoize(func: Callable) -> Callable:
    """
    A decorator to access and cache rhyme sets.

    If the word to find the rhyme set of already exists in the cache, then
    there is no need to execute `func` because results can be taken from the
    cache. Otherwise, execute `func` and store the results into the cache.
    """
    @functools.wraps(func)
    async def wrapper(
        *args,
        instance: Callable = None,
        word: str = None,
        is_instant_fail: bool = None
    ) -> Set[str]:
        with Cache(word, is_instant_fail) as (cache, word):
            if word not in cache.keys():
                cache[word] = await func(instance, word)
                logging.info(f"New word cached: {word}")
            else:
                logging.info(f"Old word used: {word}")

        return cache[word]

    return wrapper


class MarkovPoemGenerator(commands.Cog):
    """
    A cog that provides a poem by taking the markov of a corpus.

    By processing the corpus text through a markov chain, a series of lines
    can be iterated through, whilst corresponding to the given rhyme scheme.
    """

    POEM_TIMEOUT = 20  # In seconds

    SOURCES: List[str] = [
        "shakespeare_corpus.txt"
    ]

    templates: Dict[str, str] = {
        "shakespearean-sonnet": "abab/cdcd/efef/gg",
        "quads": "aaaa/bbbb/cccc/dddd/eeee"  # For testing
    }

    rhyme_websites: List[Tuple[bool, str]] = [
        # (is exact rhyme, website link)
        (True, "https://api.datamuse.com/words?rel_rhy="),
        (False, "https://api.datamuse.com/words?rel_nry=")
    ]

    def __init__(self, bot: commands.Bot):
        """Initializes the full corpus text and the markov model."""
        self.bot = bot

        # Load the full text corpus
        for source_file in self.SOURCES:
            with Path(f"bot/resources/valentines/{source_file}").open() as f:
                full_corpus = f.read().splitlines()

        # Create the markov model
        self.model = markovify.Text(full_corpus, state_size=1)

        logging.info("Full text corpus and markov model successfully loaded.")

    @staticmethod
    def _get_last_word(sentence: str) -> str:
        """Returns the last word of a sentence string."""
        if isinstance(sentence, str) is False:
            # Likely to be caused by `make_short_sentence` running out
            # and feeding it None, which is an unlikely scenario
            raise TypeError(f"Argument is a {type(sentence)} instead of a str.")
        return sentence.strip(string.punctuation).split()[-1]

    @memoize
    async def _get_rhyme_set(
        self,
        word: str,
        near_rhyme_min_score: int = 2000
    ) -> None:
        """
        Accesses web APIs to get rhymes and returns a set.

        `near_rhyme_min_score` is to filter out near rhymes that barely rhyme
        with the word. The equivalent for exact rhymes is not necessary as they
        already rhyme.

        Should additional web APIs for rhymes be added, the `min_score` needs
        to be tuned. Perhaps it should be added as an element to the tuple of
        the element of the `self.rhyme_websites` list.
        """
        rhyme_set = set()

        for is_exact, website in self.rhyme_websites:
            min_score = 0 if is_exact else near_rhyme_min_score

            async with self.bot.http_session.get(
                website + word,
                timeout=10
            ) as response:
                curr_set = set(
                    data["word"] for data in await response.json()
                    if data.get("score", 0) >= min_score
                )
                rhyme_set |= curr_set

        return rhyme_set

    async def _get_rhyming_line(
        self,
        word_rhymes: List[str],
        limiter: int = 80000
    ) -> str:
        """
        Returns a sentence string with a last word in `word_rhymes`.

        The function will continue to iterate through sentences provided by the
        markov model, until it finds one that rhymes or until it reaches the
        limiter.
        """
        curr = 0
        line = self.model.make_short_sentence(random.randint(50, 120))
        while self._get_last_word(line) not in word_rhymes:
            if curr >= limiter:
                raise RhymingSentenceNotFound

            line = self.model.make_short_sentence(random.randint(50, 120))
            curr += 1

        return line

    def _get_unit_count(self, scheme: str) -> Dict[str, bool]:
        """Checks how many times a unit occurs in a rhyme scheme."""
        return {char: scheme.count(char) for char in set(scheme)}

    async def _init_unit(
        self,
        is_last_line: bool,
        rhyme_track: Dict[str, Set[str]],
        unit: str
    ) -> str:
        rhyme_set = set()
        while len(rhyme_set) == 0:
            line = self.model.make_short_sentence(
                random.randint(50, 120)
            )

            rhyme_set = await self._get_rhyme_set(
                instance=self,
                word=self._get_last_word(line),
                is_instant_fail=(not is_last_line)
            )

        rhyme_track[unit] = rhyme_set
        return line

    @commands.command()
    async def poem(self, ctx: commands.Context, scheme: str) -> None:
        """
        Gives the user a love poem.

        Poems are often structured by a rhyme scheme, which is often split into
        stanzas. Stanzas are the equivalent of verses in modern pop songs, and
        they are separated by an empty line. The blackslash character indicates
        that an empty line should be generated to create a stanza.

        In this code, a unit is defined by a single character of the scheme. If
        two or more units are the same, they are meant to rhyme (i.e their last
        words rhyme).

        If the count of a unit is one, that means it is the last unit in the
        rhyme scheme being processed. Having no more units left means that it
        is okay for it to not have any rhymes.

        The function will run through the units of scheme. If it is a new
        scheme, the unit will be added to `rhyme_track` as a key with the value
        of the rhyme set. If a unit is found again and it is not the last in
        the scheme, then then its rhyme set will be added to `rhyme_track`.
        This is so that all the rhymes are not contingent on the first unit of
        the scheme.

        The time taken to process the command is recorded and shown in the
        footer of the embed.

        A timeout has been added to the command as a fail-safe measure if
        something freezes.
        """
        # If the `scheme` is actually a template, convert it into a scheme
        scheme = self.templates.get(scheme, scheme)
        self.scheme = scheme

        unit_count = self._get_unit_count(scheme)

        time_start = datetime.now()

        try:
            async with async_timeout.timeout(self.POEM_TIMEOUT), ctx.typing():
                stanzas = []
                acc_lines = []  # Accumulate lines before joining into a stanza
                rhyme_track = {}  # Maps units to their rhyme sets

                for unit in scheme:
                    is_last_line = True if unit_count[unit] == 1 else False

                    # Create new stanza
                    if unit == "/":
                        new_stanza = "\n".join(acc_lines)
                        stanzas.append(new_stanza)
                        acc_lines = []
                        continue

                    # Creating a line for the unit
                    if unit not in rhyme_track:
                        new_line = await self._init_unit(
                            is_last_line, rhyme_track, unit
                        )
                        acc_lines.append(new_line)
                    else:
                        new_line = await self._get_rhyming_line(
                            word_rhymes=rhyme_track[unit]
                        )
                        acc_lines.append(new_line)

                        # If last line, it will not be referred to again
                        if not is_last_line:
                            rhyme_track[unit] |= await self._get_rhyme_set(
                                instance=self,
                                word=self._get_last_word(new_line),
                                is_instant_fail=(not is_last_line)
                            )

                    unit_count[unit] -= 1

                stanzas.append("\n".join(acc_lines))  # Append final stanza

                elapsed_time = datetime.now() - time_start
                elapsed_time = elapsed_time.seconds

                poem_embed = Embed(
                    title="A Markov Poem For " + str(ctx.author.name),
                    color=Colours.pink,
                    description="\n\n".join(stanzas)
                )
                poem_embed.set_footer(text=f"Elapsed time: {elapsed_time}s\n"
                                      "Rhymes API provided by datamuse.")
                await ctx.send(embed=poem_embed)
        except TimeoutError:
            logging.warning("Poem generator timed out.")
            await ctx.send("Unlucky, try again!")

    async def cog_command_error(
        self,
        ctx: commands.Context,
        error: Exception
    ) -> None:
        """Handles Discord errors and exceptions."""
        if isinstance(error, RhymingSentenceNotFound):
            logging.warning("Rhyming sentence not found!")
            await ctx.send("Sentence failed, trying again...")
            return await self.poem(ctx, self.scheme)
        else:
            logging.error(f"Unknown error caught: {error}")


def setup(bot: commands.Bot) -> None:
    """Poem generator cog load."""
    bot.add_cog(MarkovPoemGenerator(bot))

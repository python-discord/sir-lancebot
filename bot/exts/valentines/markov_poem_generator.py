import functools
import logging
import random
import string
from asyncio import Future, TimeoutError, get_event_loop
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Callable, Dict, List, Optional, Set, Tuple, Type

import async_timeout
import markovify
from discord import Embed
from discord.ext import commands

from bot.constants import Colours
from bot.utils.pagination import LinePaginator

log = logging.getLogger(__name__)

_EXECUTOR = ThreadPoolExecutor(10)


async def in_thread(func: Callable) -> Future:
    """Allows non-async functions to work in async functions."""
    loop = get_event_loop()
    return await loop.run_in_executor(_EXECUTOR, func)


class MakeShortSentenceRanOut(commands.CommandError):
    """Raised when the markov chain can no longer output sentences."""

    pass


class RhymingSentenceNotFound(commands.CommandError):
    """Raised when a rhyming sentence could not be found."""

    def __init__(
        self,
        scheme: str,
        unit_count: Dict[str, int],
        time_start: datetime.time
    ):
        self.scheme = scheme
        self.unit_count = unit_count
        self.time_start = time_start


class RhymeAPIUnresponsive(commands.CommandError):
    """Raised when the API does not return 200."""

    pass


class Cache:
    """A context manager to facilitate the storage of word to rhyme sets."""

    cache: Dict[str, Set[str]] = {}

    def __init__(self, word: str):
        self.word = word

    def __enter__(self):
        self.word = self.word.replace("'", "e")  # Sometimes ' replaces e
        return self.cache, self.word

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType]
    ):
        # If an error is raised, then the word may not be added to the cache.
        if self.word in self.cache and len(self.cache[self.word]) == 0:
            logging.info(f"No rhymes were found for the word: {self.word}")


def memoize(func: Callable) -> Callable:
    """
    A decorator to access and cache rhyme sets.

    If the rhyme set of the word already exists in the cache, then
    there is no need to execute `func` because results can be taken from the
    cache. Otherwise, execute `func` and store the results into the cache.
    """
    @functools.wraps(func)
    async def wrapper(
        *args,
        instance: Callable = None,
        word: str = None
    ) -> Set[str]:
        with Cache(word) as (cache, word):
            if word not in cache.keys():
                cache[word] = await func(instance, word)

        return cache[word]

    return wrapper


def command_wrapper(func: Callable) -> Callable:
    """The decorator adds a timeout and shows the bot's `typing...` text."""
    @functools.wraps(func)
    async def wrapper(
        *args,
        instance: Callable = None,
        timeout: int = None,
        ctx: commands.Context = None,
        scheme: str = None,
        unit_count: Dict[str, int] = None,
        time_start: datetime.time = None,
        is_first_error: bool = None
    ) -> Callable:
        try:
            async with async_timeout.timeout(timeout), ctx.typing():
                return await func(instance, ctx, scheme, unit_count,
                                  time_start, is_first_error)
        except TimeoutError:
            await ctx.send(f"Sorry {ctx.author.mention}, but your poem"
                           " timed out, please try again!")

    return wrapper


class MarkovPoemGenerator(commands.Cog):
    """
    A cog that provides a poem by taking the markov of a corpus.

    By processing the corpus text through a markov chain, a series of lines
    can be iterated through, whilst corresponding to the given rhyme scheme.
    """

    POEM_TIMEOUT = 30  # In seconds
    near_rhyme_min_score = 2000
    rhyming_line_finder_limiter = 20000
    max_char_range = (50, 120)  # For the sentence generator

    SOURCES: List[str] = [
        "shakespeare_corpus.txt"
    ]

    templates: Dict[str, str] = {
        "shakespearean-sonnet": "abab/cdcd/efef/gg",
        "spenserian-sonnet": "abab/bcbc/cdcd/ee",
        "petrarch-sonnet": "abbaabba/cdecde",
        "ballade": "ababbcbc",
        "terza-rima": "aba/bcb/cdc/ded/ee",
        "villanelle": "aba/aba/aba/aba/aba/abaa",
        "limerick": "aabba"
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
    def _get_unit_count(scheme: str) -> Dict[str, int]:
        """Checks how many times a unit occurs in a rhyme scheme."""
        return {char: scheme.count(char) for char in set(scheme)}

    @staticmethod
    def _get_last_word(sentence: str) -> str:
        """Returns the last word of a sentence string."""
        return sentence.strip(string.punctuation).split()[-1]

    async def _get_sentence(self) -> str:
        """
        Uses `in_thread` to return a sentence asynchronously.

        The sentence is generated via the markov chain.
        """
        def func() -> str:
            line = self.model.make_short_sentence(
                random.randint(*self.max_char_range)
            )

            if not isinstance(line, str):
                logging.error(f"Argument is a {type(line)} instead of a str.")
                raise MakeShortSentenceRanOut

            return line

        return await in_thread(func)

    @memoize
    async def _get_rhyme_set(
        self,
        word: str,
        near_rhyme_min_score: int = near_rhyme_min_score
    ) -> Set[str]:
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
                if response.status != 200:  # 200 means 'ok'
                    logging.warning(
                        f"Received response {response.status} "
                        f"from: {website + word}"
                    )
                    raise RhymeAPIUnresponsive
                curr_set = set(
                    data["word"] for data in await response.json()
                    if data.get("score", 0) >= min_score
                )
                rhyme_set |= curr_set

        return rhyme_set

    @staticmethod
    async def _handle_rhyming_sentence_not_found(
        ctx: commands.Context,
        is_first_error: bool,
        scheme: str,
        unit_count: Dict[str, int],
        time_start: datetime.time
    ) -> None:
        """Updates the user and raises the error."""
        if is_first_error:
            await ctx.send(
                f"Sorry {ctx.author.mention}, but the rhymes are"
                " really tricky, your poem is going to take a while..."
            )
        else:
            await ctx.send(
                f"Apologies {ctx.author.mention}, but the rhymes for that poem"
                " were really not matching up. Could you please try the"
                " command again?"
            )
        raise RhymingSentenceNotFound(scheme, unit_count, time_start)

    async def _get_rhyming_line(
        self,
        word_rhymes: List[str],
        existing_lines: List[str],
        error_info: Tuple[commands.Context, bool, str, Dict[str, int],
                          datetime.time],
        limiter: int = rhyming_line_finder_limiter
    ) -> str:
        """
        Returns a sentence string with a last word in `word_rhymes`.

        The function will continue to iterate through sentences provided by the
        markov model, until it finds one that rhymes or until it reaches the
        limiter.

        The function also prevents the same line from appearing twice.
        """
        curr = 0

        line = await self._get_sentence()
        while (self._get_last_word(line) not in word_rhymes
               and line not in existing_lines):
            if curr >= limiter:
                await self._handle_rhyming_sentence_not_found(*error_info)

            line = await self._get_sentence()
            curr += 1
        return line

    async def _init_unit(
        self,
        rhyme_track: Dict[str, Set[str]],
        unit: str,
        is_last_line: bool
    ) -> str:
        """
        Returns a line with a last word that has a rhyme set.

        If there is only one line in this unit, then the last word does not
        need a rhyme set.
        """
        rhyme_set = set()

        async def _get_line_and_rhyme_set() -> Tuple[str, Set[str]]:
            line = await self._get_sentence()

            rhyme_set = await self._get_rhyme_set(
                instance=self,
                word=self._get_last_word(line)
            )

            return line, rhyme_set

        if is_last_line:
            line, rhyme_set = await _get_line_and_rhyme_set()
        else:
            while len(rhyme_set) == 0:
                line, rhyme_set = await _get_line_and_rhyme_set()

        rhyme_track[unit] = rhyme_set
        return line

    @command_wrapper
    async def _get_generated_markov_poem(
        self,
        ctx: commands.Context,
        scheme: str,
        unit_count: Dict[str, int],
        time_start: datetime.time,
        is_first_error: bool
    ) -> List[str]:
        """
        Generates a love poem with the markov chain and sends it off.

        If the count of a unit is one, that means it is the last unit in the
        rhyme scheme being processed.

        The function will iterate through the units of scheme. If it is a new
        unit, it will be added to `rhyme_track` as a key with the rhyme set
        as the value. If a unit is found again, then then the last word of the
        new line's rhyme set will be added to `rhyme_track`. This is so that
        all the rhymes are not contingent on the first unit of the scheme.
        """
        lines = []
        rhyme_track = {}  # Maps units to their accumulative rhyme sets

        for unit in scheme:
            # `last_line` means last line of a rhyme group
            is_last_line = True if unit_count[unit] == 1 else False

            # Create new stanza
            if unit == "/":
                lines.append("")
                continue

            # Creating a line for the unit
            if unit not in rhyme_track:
                new_line = await self._init_unit(
                    rhyme_track, unit, is_last_line
                )
                lines.append(new_line)
            else:
                new_line = await self._get_rhyming_line(
                    word_rhymes=rhyme_track[unit],
                    existing_lines=lines,
                    error_info=(ctx, is_first_error, scheme, unit_count,
                                time_start)
                )
                lines.append(new_line)

                # If last line, it will not be referred to again
                if not is_last_line:
                    rhyme_track[unit] |= await self._get_rhyme_set(
                        instance=self,
                        word=self._get_last_word(new_line)
                    )

            unit_count[unit] -= 1

        return lines

    async def send_markov_poem(
        self,
        ctx: commands.Context,
        scheme: str,
        unit_count: Dict[str, int],
        time_start: datetime.time,
        is_first_error: bool = True
    ) -> None:
        """Gives the user a paginated embed of their markov poem."""
        lines = await self._get_generated_markov_poem(
            instance=self,
            timeout=self.POEM_TIMEOUT,
            ctx=ctx,
            scheme=scheme,
            unit_count=unit_count,
            time_start=time_start,
            is_first_error=is_first_error
        )

        elapsed_time = datetime.now() - time_start
        elapsed_time = elapsed_time.seconds

        poem_embed = Embed(
            title="A Markov Poem For " + str(ctx.author.name),
            color=Colours.soft_red
        )

        await LinePaginator.paginate(
            lines,
            ctx,
            poem_embed,
            max_lines=31,
            max_size=1000,
            empty=False,
            footer_text=f"Elapsed time: {elapsed_time}s\n"
                        "Rhymes API provided by datamuse."
        )

    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.command(
        aliases=("poem", "mpoem", "m_poem", "markpoem", "mark_poem"),
        help=f"""This command generates a poem via a markov chain, and all you
            have to do is provide a rhyme scheme.

            The rhyme scheme is made from characters separated by slashes. E.g
            "abab/cdcd/efef/gg". The slashes denote a new stanza, i.e, they
            create an empty line. Same characters mean that the lines rhyme.
            Note that the characters are case sensitive! For example, a and A
            represent two different rhyme schemes.

            You may also use our existing rhyme scheme templates:
            {chr(10).join((k + " --- " + v) for k, v in templates.items())}""",
        brief="Gives the user a love poem made with a markov chain."
    )
    async def markov_poem(
        self,
        ctx: commands.Context,
        rhyme_scheme: str
    ) -> None:
        """
        Gives the user a love poem based on a rhyme_scheme.

        The user's `rhyme_scheme` is processed before being placed into the
        poem generation process.

        In this code, a unit is defined by a single character of the scheme. If
        two or more units are the same, they are meant to rhyme (i.e their last
        words rhyme).

        The time taken to process the command is recorded and shown in the
        footer of the embed.
        """
        scheme = rhyme_scheme.lower()
        scheme = self.templates.get(scheme, scheme)
        unit_count = self._get_unit_count(scheme)
        time_start = datetime.now()

        await self.send_markov_poem(ctx, scheme, unit_count, time_start)

    async def cog_command_error(
        self,
        ctx: commands.Context,
        error: Exception
    ) -> None:
        """Handles Discord errors and exceptions."""
        if isinstance(error, RhymingSentenceNotFound):
            error.handled = True
            await self.send_markov_poem(
                ctx, error.scheme, error.unit_count, error.time_start,
                is_first_error=False
            )
        elif isinstance(error, RhymeAPIUnresponsive):
            error.handled = True
            embed = Embed(
                title="Uh oh... Markov Poem can\'t give you a poem...",
                color=Colours.soft_red,
                description=f"""
                    I am sorry {ctx.author.mention}, but it looks like the API
                    that is used to help make your poems is down...
                    Please come back another time.
                    """
            )
            await ctx.send(embed=embed)
        elif isinstance(error, MakeShortSentenceRanOut):
            error.handled = True
            embed = Embed(
                title="Uh oh... Markov Poem can\'t give you a poem...",
                color=Colours.soft_red,
                description=f"""
                    Apologies {ctx.author.mention},
                    but it appears that we have encountered a rare bug.
                    It might be the case that your poem is too long,
                    please try again.
                    """
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.errors.MaxConcurrencyReached):
            error.handled = True
            await ctx.send(f"Please be patient {ctx.author.mention},"
                           " we are currently working on your poem!")


def setup(bot: commands.Bot) -> None:
    """Poem generator cog load."""
    bot.add_cog(MarkovPoemGenerator(bot))

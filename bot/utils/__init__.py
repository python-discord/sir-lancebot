import asyncio
import contextlib
import re
import string
from collections.abc import Iterable
from datetime import UTC, datetime

import discord
from discord.ext.commands import BadArgument, Context

from bot.constants import Client, Month
from bot.utils.pagination import LinePaginator


def human_months(months: Iterable[Month]) -> str:
    """Build a comma separated list of `months`."""
    return ", ".join(str(m) for m in months)


def resolve_current_month() -> Month:
    """
    Determine current month w.r.t. `Client.month_override` env var.

    If the env variable was set, current month always resolves to the configured value.
    Otherwise, the current UTC month is given.
    """
    if Client.month_override is not None:
        return Month(Client.month_override)
    return Month(datetime.now(tz=UTC).month)


async def disambiguate(
    ctx: Context,
    entries: list[str],
    *,
    timeout: float = 30,
    entries_per_page: int = 20,
    empty: bool = False,
    embed: discord.Embed | None = None
) -> str:
    """
    Has the user choose between multiple entries in case one could not be chosen automatically.

    Disambiguation will be canceled after `timeout` seconds.

    This will raise a BadArgument if entries is empty, if the disambiguation event times out,
    or if the user makes an invalid choice.
    """
    if len(entries) == 0:
        raise BadArgument("No matches found.")

    if len(entries) == 1:
        return entries[0]

    choices = (f"{index}: {entry}" for index, entry in enumerate(entries, start=1))

    def check(message: discord.Message) -> bool:
        return (
            message.content.isdecimal()
            and message.author == ctx.author
            and message.channel == ctx.channel
        )

    try:
        if embed is None:
            embed = discord.Embed()

        coro1 = ctx.bot.wait_for("message", check=check, timeout=timeout)
        coro2 = LinePaginator.paginate(
            choices, ctx, embed=embed, max_lines=entries_per_page,
            empty=empty, max_size=6000, timeout=9000
        )

        # wait_for timeout will go to except instead of the wait_for thing as I expected
        futures = [asyncio.ensure_future(coro1), asyncio.ensure_future(coro2)]
        done, pending = await asyncio.wait(futures, return_when=asyncio.FIRST_COMPLETED, loop=ctx.bot.loop)

        # :yert:
        result = next(iter(done)).result()

        # Pagination was canceled - result is None
        if result is None:
            for coro in pending:
                coro.cancel()
            raise BadArgument("Canceled.")

        # Pagination was not initiated, only one page
        if result.author == ctx.bot.user:
            # Continue the wait_for
            result = await next(iter(pending))

        # Love that duplicate code
        for coro in pending:
            coro.cancel()
    except asyncio.TimeoutError:
        raise BadArgument("Timed out.")

    # Guaranteed to not error because of isdecimal() in check
    index = int(result.content)

    try:
        return entries[index - 1]
    except IndexError:
        raise BadArgument("Invalid choice.")


def replace_many(
    sentence: str, replacements: dict, *, ignore_case: bool = False, match_case: bool = False
) -> str:
    """
    Replaces multiple substrings in a string given a mapping of strings.

    By default replaces long strings before short strings, and lowercase before uppercase.
    Example:
        var = replace_many("This is a sentence", {"is": "was", "This": "That"})
        assert var == "That was a sentence"

    If `ignore_case` is given, does a case insensitive match.
    Example:
        var = replace_many("THIS is a sentence", {"IS": "was", "tHiS": "That"}, ignore_case=True)
        assert var == "That was a sentence"

    If `match_case` is given, matches the case of the replacement with the replaced word.
    Example:
        var = replace_many(
            "This IS a sentence", {"is": "was", "this": "that"}, ignore_case=True, match_case=True
        )
        assert var == "That WAS a sentence"
    """
    if ignore_case:
        replacements = {
            word.lower(): replacement for word, replacement in replacements.items()
        }

    words_to_replace = sorted(replacements, key=lambda s: (-len(s), s))

    # Join and compile words to replace into a regex
    pattern = "|".join(re.escape(word) for word in words_to_replace)
    regex = re.compile(pattern, re.I if ignore_case else 0)

    def _repl(match: re.Match) -> str:
        """Returns replacement depending on `ignore_case` and `match_case`."""
        word = match.group(0)
        replacement = replacements[word.lower() if ignore_case else word]

        if not match_case:
            return replacement

        # Clean punctuation from word so string methods work
        cleaned_word = word.translate(str.maketrans("", "", string.punctuation))
        if cleaned_word.isupper():
            return replacement.upper()
        if cleaned_word[0].isupper():
            return replacement.capitalize()
        return replacement.lower()

    return regex.sub(_repl, sentence)


@contextlib.asynccontextmanager
async def unlocked_role(role: discord.Role, delay: int = 5) -> None:
    """
    Create a context in which `role` is unlocked, relocking it automatically after use.

    A configurable `delay` is added before yielding the context and directly after exiting the
    context to allow the role settings change to properly propagate at Discord's end. This
    prevents things like role mentions from failing because of synchronization issues.

    Usage:
    >>> async with unlocked_role(role, delay=5):
    ...     await ctx.send(f"Hey {role.mention}, free pings for everyone!")
    """
    await role.edit(mentionable=True)
    await asyncio.sleep(delay)
    try:
        yield
    finally:
        await asyncio.sleep(delay)
        await role.edit(mentionable=False)

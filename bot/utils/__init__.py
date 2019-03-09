import asyncio
from typing import List

import discord
from discord.ext.commands import BadArgument, Context

from bot.pagination import LinePaginator


async def disambiguate(
        ctx: Context, entries: List[str], *, timeout: float = 30,
        per_page: int = 20, empty: bool = False, embed: discord.Embed = None
):
    """
    Has the user choose between multiple entries in case one could not be chosen automatically.

    This will raise a BadArgument if entries is empty, if the disambiguation event times out,
    or if the user makes an invalid choice.

    :param ctx: Context object from discord.py
    :param entries: List of items for user to choose from
    :param timeout: Number of seconds to wait before canceling disambiguation
    :param per_page: Entries per embed page
    :param empty: Whether the paginator should have an extra line between items
    :param embed: The embed that the paginator will use.
    :return: Users choice for correct entry.
    """
    if len(entries) == 0:
        raise BadArgument('No matches found.')

    if len(entries) == 1:
        return entries[0]

    choices = (f'{index}: {entry}' for index, entry in enumerate(entries, start=1))

    def check(message):
        return (message.content.isdigit()
                and message.author == ctx.author
                and message.channel == ctx.channel)

    try:
        if embed is None:
            embed = discord.Embed()

        coro1 = ctx.bot.wait_for('message', check=check, timeout=timeout)
        coro2 = LinePaginator.paginate(choices, ctx, embed=embed, max_lines=per_page,
                                       empty=empty, max_size=6000, timeout=9000)

        # wait_for timeout will go to except instead of the wait_for thing as I expected
        futures = [asyncio.ensure_future(coro1), asyncio.ensure_future(coro2)]
        done, pending = await asyncio.wait(futures, return_when=asyncio.FIRST_COMPLETED, loop=ctx.bot.loop)

        # :yert:
        result = list(done)[0].result()

        # Pagination was canceled - result is None
        if result is None:
            for coro in pending:
                coro.cancel()
            raise BadArgument('Canceled.')

        # Pagination was not initiated, only one page
        if result.author == ctx.bot.user:
            # Continue the wait_for
            result = await list(pending)[0]

        # Love that duplicate code
        for coro in pending:
            coro.cancel()
    except asyncio.TimeoutError:
        raise BadArgument('Timed out.')

    # Guaranteed to not error because of isdigit() in check
    index = int(result.content)

    try:
        return entries[index - 1]
    except IndexError:
        raise BadArgument('Invalid choice.')

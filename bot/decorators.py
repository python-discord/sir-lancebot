import logging
import random
import typing
from asyncio import Lock
from functools import wraps
from weakref import WeakValueDictionary

from discord import Colour, Embed
from discord.ext import commands
from discord.ext.commands import CheckFailure, Context

from bot.constants import ERROR_REPLIES

log = logging.getLogger(__name__)


class InChannelCheckFailure(CheckFailure):
    """Check failure when the user runs a command in a non-whitelisted channel."""

    pass


def with_role(*role_ids: int) -> bool:
    """Check to see whether the invoking user has any of the roles specified in role_ids."""
    async def predicate(ctx: Context) -> bool:
        if not ctx.guild:  # Return False in a DM
            log.debug(
                f"{ctx.author} tried to use the '{ctx.command.name}'command from a DM. "
                "This command is restricted by the with_role decorator. Rejecting request."
            )
            return False

        for role in ctx.author.roles:
            if role.id in role_ids:
                log.debug(f"{ctx.author} has the '{role.name}' role, and passes the check.")
                return True

        log.debug(
            f"{ctx.author} does not have the required role to use "
            f"the '{ctx.command.name}' command, so the request is rejected."
        )
        return False
    return commands.check(predicate)


def without_role(*role_ids: int) -> bool:
    """Check whether the invoking user does not have all of the roles specified in role_ids."""
    async def predicate(ctx: Context) -> bool:
        if not ctx.guild:  # Return False in a DM
            log.debug(
                f"{ctx.author} tried to use the '{ctx.command.name}' command from a DM. "
                "This command is restricted by the without_role decorator. Rejecting request."
            )
            return False

        author_roles = [role.id for role in ctx.author.roles]
        check = all(role not in author_roles for role in role_ids)
        log.debug(
            f"{ctx.author} tried to call the '{ctx.command.name}' command. "
            f"The result of the without_role check was {check}."
        )
        return check
    return commands.check(predicate)


def in_channel_check(*channels: int, bypass_roles: typing.Container[int] = None) -> typing.Callable[[Context], bool]:
    """Checks that the message is in a whitelisted channel or optionally has a bypass role."""
    def predicate(ctx: Context) -> bool:
        if not ctx.guild:
            log.debug(f"{ctx.author} tried to use the '{ctx.command.name}' command from a DM.")
            return True

        if ctx.channel.id in channels:
            log.debug(
                f"{ctx.author} tried to call the '{ctx.command.name}' command "
                f"and the command was used in a whitelisted channel."
            )
            return True

        if hasattr(ctx.command.callback, "in_channel_override"):
            log.debug(
                f"{ctx.author} called the '{ctx.command.name}' command "
                f"and the command was whitelisted to bypass the in_channel check."
            )
            return True

        if bypass_roles and any(r.id in bypass_roles for r in ctx.author.roles):
            log.debug(
                f"{ctx.author} called the '{ctx.command.name}' command and "
                f"had a role to bypass the in_channel check."
            )
            return True

        log.debug(
            f"{ctx.author} tried to call the '{ctx.command.name}' command. "
            f"The in_channel check failed."
        )

        channels_str = ', '.join(f"<#{c_id}>" for c_id in channels)
        raise InChannelCheckFailure(
            f"Sorry, but you may only use this command within {channels_str}."
        )

    return predicate


in_channel = commands.check(in_channel_check)


def override_in_channel(func: typing.Callable) -> typing.Callable:
    """
    Set command callback attribute for detection in `in_channel_check`.

    This decorator has to go before (below) below the `command` decorator.
    """
    func.in_channel_override = True
    return func


def locked():
    """
    Allows the user to only run one instance of the decorated command at a time.

    Subsequent calls to the command from the same author are ignored until the command has completed invocation.

    This decorator has to go before (below) the `command` decorator.
    """
    def wrap(func: typing.Callable):
        func.__locks = WeakValueDictionary()

        @wraps(func)
        async def inner(self, ctx: Context, *args, **kwargs):
            lock = func.__locks.setdefault(ctx.author.id, Lock())
            if lock.locked():
                embed = Embed()
                embed.colour = Colour.red()

                log.debug(f"User tried to invoke a locked command.")
                embed.description = (
                    "You're already using this command. Please wait until "
                    "it is done before you use it again."
                )
                embed.title = random.choice(ERROR_REPLIES)
                await ctx.send(embed=embed)
                return

            async with func.__locks.setdefault(ctx.author.id, Lock()):
                return await func(self, ctx, *args, **kwargs)
        return inner
    return wrap

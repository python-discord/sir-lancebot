import asyncio
import functools
import logging
import random
import typing
from asyncio import Lock
from datetime import datetime
from functools import wraps
from weakref import WeakValueDictionary

from discord import Colour, Embed
from discord.ext import commands
from discord.ext.commands import CheckFailure, Context

from bot.constants import Client, ERROR_REPLIES, Month

ONE_DAY = 24 * 60 * 60

log = logging.getLogger(__name__)


class InChannelCheckFailure(CheckFailure):
    """Check failure when the user runs a command in a non-whitelisted channel."""

    pass


class InMonthCheckFailure(CheckFailure):
    """Check failure for when a command is invoked outside of its allowed month."""

    pass


def seasonal_task(*allowed_months: Month, sleep_time: typing.Union[float, int] = ONE_DAY) -> typing.Callable:
    """
    Perform the decorated method periodically in `allowed_months`.

    This provides a convenience wrapper to avoid code repetition where some task shall
    perform an operation repeatedly in a constant interval, but only in specific months.

    The decorated function will be called once every `sleep_time` seconds while
    the current UTC month is in `allowed_months`. Sleep time defaults to 24 hours.

    The wrapped task is responsible for waiting for the bot to be ready, if necessary.
    """
    def decorator(task_body: typing.Callable) -> typing.Callable:
        @functools.wraps(task_body)
        async def decorated_task(*args, **kwargs) -> None:
            """Call `task_body` once every `sleep_time` seconds in `allowed_months`."""
            log.info(f"Starting seasonal task {task_body.__qualname__} ({allowed_months})")

            while True:
                current_month = Month(datetime.utcnow().month)

                if current_month in allowed_months:
                    await task_body(*args, **kwargs)
                else:
                    log.debug(f"Seasonal task {task_body.__qualname__} sleeps in {current_month.name}")

                await asyncio.sleep(sleep_time)
        return decorated_task
    return decorator


def in_month_listener(*allowed_months: Month) -> typing.Callable:
    """
    Shield a listener from being invoked outside of `allowed_months`.

    The check is performed against current UTC month.
    """
    def decorator(listener: typing.Callable) -> typing.Callable:
        @functools.wraps(listener)
        async def guarded_listener(*args, **kwargs) -> None:
            """Wrapped listener will abort if not in allowed month."""
            current_month = Month(datetime.utcnow().month)

            if current_month in allowed_months:
                # Propagate return value although it should always be None
                return await listener(*args, **kwargs)
            else:
                log.debug(f"Guarded {listener.__qualname__} from invoking in {current_month.name}")
        return guarded_listener
    return decorator


def in_month_command(*allowed_months: Month) -> typing.Callable:
    """
    Check whether the command was invoked in one of `enabled_months`.

    Uses the current UTC month at the time of running the predicate.
    """
    async def predicate(ctx: Context) -> bool:
        current_month = datetime.utcnow().month
        can_run = current_month in allowed_months

        human_months = ", ".join(m.name for m in allowed_months)
        log.debug(
            f"Command '{ctx.command}' is locked to months {human_months}. "
            f"Invoking it in month {current_month} is {'allowed' if can_run else 'disallowed'}."
        )
        if can_run:
            return True
        else:
            raise InMonthCheckFailure(f"Command can only be used in {human_months}")

    return commands.check(predicate)


def with_role(*role_ids: int) -> typing.Callable:
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


def without_role(*role_ids: int) -> typing.Callable:
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
    """
    Checks that the message is in a whitelisted channel or optionally has a bypass role.

    If `in_channel_override` is present, check if it contains channels
    and use them in place of the global whitelist.
    """
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

        if bypass_roles and any(r.id in bypass_roles for r in ctx.author.roles):
            log.debug(
                f"{ctx.author} called the '{ctx.command.name}' command and "
                f"had a role to bypass the in_channel check."
            )
            return True

        if hasattr(ctx.command.callback, "in_channel_override"):
            override = ctx.command.callback.in_channel_override
            if override is None:
                log.debug(
                    f"{ctx.author} called the '{ctx.command.name}' command "
                    f"and the command was whitelisted to bypass the in_channel check."
                )
                return True
            else:
                if ctx.channel.id in override:
                    log.debug(
                        f"{ctx.author} tried to call the '{ctx.command.name}' command "
                        f"and the command was used in an overridden whitelisted channel."
                    )
                    return True

                log.debug(
                    f"{ctx.author} tried to call the '{ctx.command.name}' command. "
                    f"The overridden in_channel check failed."
                )
                channels_str = ', '.join(f"<#{c_id}>" for c_id in override)
                raise InChannelCheckFailure(
                    f"Sorry, but you may only use this command within {channels_str}."
                )

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


def override_in_channel(channels: typing.Tuple[int] = None) -> typing.Callable:
    """
    Set command callback attribute for detection in `in_channel_check`.

    Override global whitelist if channels are specified.

    This decorator has to go before (below) below the `command` decorator.
    """
    def inner(func: typing.Callable) -> typing.Callable:
        func.in_channel_override = channels
        return func

    return inner


def locked() -> typing.Union[typing.Callable, None]:
    """
    Allows the user to only run one instance of the decorated command at a time.

    Subsequent calls to the command from the same author are ignored until the command has completed invocation.

    This decorator has to go before (below) the `command` decorator.
    """
    def wrap(func: typing.Callable) -> typing.Union[typing.Callable, None]:
        func.__locks = WeakValueDictionary()

        @wraps(func)
        async def inner(self: typing.Callable, ctx: Context, *args, **kwargs) -> typing.Union[typing.Callable, None]:
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


def mock_in_debug(return_value: typing.Any) -> typing.Callable:
    """
    Short-circuit function execution if in debug mode and return `return_value`.

    The original function name, and the incoming args and kwargs are DEBUG level logged
    upon each call. This is useful for expensive operations, i.e. media asset uploads
    that are prone to rate-limits but need to be tested extensively.
    """
    def decorator(func: typing.Callable) -> typing.Callable:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs) -> typing.Any:
            """Short-circuit and log if in debug mode."""
            if Client.debug:
                log.debug(f"Function {func.__name__} called with args: {args}, kwargs: {kwargs}")
                return return_value
            return await func(*args, **kwargs)
        return wrapped
    return decorator

import datetime
import logging
from typing import Callable, Container, Iterable, Optional

from discord.ext.commands import (
    BucketType,
    CheckFailure,
    Cog,
    Command,
    CommandOnCooldown,
    Context,
    Cooldown,
    CooldownMapping,
)

from bot import constants

log = logging.getLogger(__name__)


class InWhitelistCheckFailure(CheckFailure):
    """Raised when the `in_whitelist` check fails."""

    def __init__(self, redirect_channel: Optional[int]) -> None:
        self.redirect_channel = redirect_channel

        if redirect_channel:
            redirect_message = f" here. Please use the <#{redirect_channel}> channel instead"
        else:
            redirect_message = ""

        error_message = f"You are not allowed to use that command{redirect_message}."

        super().__init__(error_message)


def in_whitelist_check(
    ctx: Context,
    channels: Container[int] = (),
    categories: Container[int] = (),
    roles: Container[int] = (),
    redirect: Optional[int] = constants.Channels.community_bot_commands,
    fail_silently: bool = False,
) -> bool:
    """
    Check if a command was issued in a whitelisted context.

    The whitelists that can be provided are:

    - `channels`: a container with channel ids for whitelisted channels
    - `categories`: a container with category ids for whitelisted categories
    - `roles`: a container with with role ids for whitelisted roles

    If the command was invoked in a context that was not whitelisted, the member is either
    redirected to the `redirect` channel that was passed (default: #bot-commands) or simply
    told that they're not allowed to use this particular command (if `None` was passed).
    """
    if redirect and redirect not in channels:
        # It does not make sense for the channel whitelist to not contain the redirection
        # channel (if applicable). That's why we add the redirection channel to the `channels`
        # container if it's not already in it. As we allow any container type to be passed,
        # we first create a tuple in order to safely add the redirection channel.
        #
        # Note: It's possible for the redirect channel to be in a whitelisted category, but
        # there's no easy way to check that and as a channel can easily be moved in and out of
        # categories, it's probably not wise to rely on its category in any case.
        channels = tuple(channels) + (redirect,)

    if channels and ctx.channel.id in channels:
        log.trace(f"{ctx.author} may use the `{ctx.command.name}` command as they are in a whitelisted channel.")
        return True

    # Only check the category id if we have a category whitelist and the channel has a `category_id`
    if categories and hasattr(ctx.channel, "category_id") and ctx.channel.category_id in categories:
        log.trace(f"{ctx.author} may use the `{ctx.command.name}` command as they are in a whitelisted category.")
        return True

    category = getattr(ctx.channel, "category", None)
    if category and category.name == constants.codejam_categories_name:
        log.trace(f"{ctx.author} may use the `{ctx.command.name}` command as they are in a codejam team channel.")
        return True

    # Only check the roles whitelist if we have one and ensure the author's roles attribute returns
    # an iterable to prevent breakage in DM channels (for if we ever decide to enable commands there).
    if roles and any(r.id in roles for r in getattr(ctx.author, "roles", ())):
        log.trace(f"{ctx.author} may use the `{ctx.command.name}` command as they have a whitelisted role.")
        return True

    log.trace(f"{ctx.author} may not use the `{ctx.command.name}` command within this context.")

    # Some commands are secret, and should produce no feedback at all.
    if not fail_silently:
        raise InWhitelistCheckFailure(redirect)
    return False


def with_role_check(ctx: Context, *role_ids: int) -> bool:
    """Returns True if the user has any one of the roles in role_ids."""
    if not ctx.guild:  # Return False in a DM
        log.trace(
            f"{ctx.author} tried to use the '{ctx.command.name}'command from a DM. "
            "This command is restricted by the with_role decorator. Rejecting request."
        )
        return False

    for role in ctx.author.roles:
        if role.id in role_ids:
            log.trace(f"{ctx.author} has the '{role.name}' role, and passes the check.")
            return True

    log.trace(
        f"{ctx.author} does not have the required role to use "
        f"the '{ctx.command.name}' command, so the request is rejected."
    )
    return False


def without_role_check(ctx: Context, *role_ids: int) -> bool:
    """Returns True if the user does not have any of the roles in role_ids."""
    if not ctx.guild:  # Return False in a DM
        log.trace(
            f"{ctx.author} tried to use the '{ctx.command.name}' command from a DM. "
            "This command is restricted by the without_role decorator. Rejecting request."
        )
        return False

    author_roles = [role.id for role in ctx.author.roles]
    check = all(role not in author_roles for role in role_ids)
    log.trace(
        f"{ctx.author} tried to call the '{ctx.command.name}' command. "
        f"The result of the without_role check was {check}."
    )
    return check


def cooldown_with_role_bypass(rate: int, per: float, type: BucketType = BucketType.default, *,
                              bypass_roles: Iterable[int]) -> Callable:
    """
    Applies a cooldown to a command, but allows members with certain roles to be ignored.

    NOTE: this replaces the `Command.before_invoke` callback, which *might* introduce problems in the future.
    """
    # Make it a set so lookup is hash based.
    bypass = set(bypass_roles)

    # This handles the actual cooldown logic.
    buckets = CooldownMapping(Cooldown(rate, per, type))

    # Will be called after the command has been parse but before it has been invoked, ensures that
    # the cooldown won't be updated if the user screws up their input to the command.
    async def predicate(cog: Cog, ctx: Context) -> None:
        nonlocal bypass, buckets

        if any(role.id in bypass for role in ctx.author.roles):
            return

        # Cooldown logic, taken from discord.py internals.
        current = ctx.message.created_at.replace(tzinfo=datetime.timezone.utc).timestamp()
        bucket = buckets.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit(current)
        if retry_after:
            raise CommandOnCooldown(bucket, retry_after)

    def wrapper(command: Command) -> Command:
        # NOTE: this could be changed if a subclass of Command were to be used. I didn't see the need for it
        # so I just made it raise an error when the decorator is applied before the actual command object exists.
        #
        # If the `before_invoke` detail is ever a problem then I can quickly just swap over.
        if not isinstance(command, Command):
            raise TypeError(
                "Decorator `cooldown_with_role_bypass` must be applied after the command decorator. "
                "This means it has to be above the command decorator in the code."
            )

        command._before_invoke = predicate

        return command

    return wrapper

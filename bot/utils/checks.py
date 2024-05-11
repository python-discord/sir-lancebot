from collections.abc import Container

from discord.ext.commands import (
    Context,
)
from pydis_core.utils.checks import in_whitelist_check as core_in_whitelist_check
from pydis_core.utils.logging import get_logger

from bot import constants

log = get_logger(__name__)
CODEJAM_CATEGORY_NAME = "Code Jam"


def in_whitelist_check(
    ctx: Context,
    channels: Container[int] = (),
    categories: Container[int] = (),
    roles: Container[int] = (),
    redirect: int | None = constants.Channels.sir_lancebot_playground,
    fail_silently: bool = False,
) -> bool:
    """
    Check if a command was issued in a whitelisted context.

    Check bot-core's in_whitelist_check docstring for more details.
    """
    return core_in_whitelist_check(
        ctx=ctx, channels=channels, categories=categories, roles=roles, redirect=redirect, fail_silently=fail_silently
    )


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

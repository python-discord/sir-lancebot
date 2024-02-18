from typing import NoReturn

from discord import Interaction
from discord.ext.commands import BadArgument, Context
from pydis_core.utils.error_handling.commands import AbstractCommandErrorHandler

from ._utils import create_error_embed, get_parent_command_and_subcontext, revert_cooldown_counter


class BadArgumentErrorHandler(AbstractCommandErrorHandler):
    """An handler for the BadArgument error."""

    async def should_handle_error(self, error: Exception) -> bool:
        """A predicate that determines whether the error should be handled or not."""
        return isinstance(error, BadArgument)

    async def handle_text_command_error(self, context: Context, error: Exception) -> NoReturn:
        """Handle error raised in the context of text commands."""
        revert_cooldown_counter(context.command, context.message)
        parent_command, ctx = get_parent_command_and_subcontext(context)
        embed = create_error_embed(
            "The argument you provided was invalid: "
            f"{error}\n\nUsage:\n```\n{ctx.prefix}{parent_command}{ctx.command} {ctx.command.signature}\n```"
        )
        await context.send(embed=embed)

    async def handle_app_command_error(self, interaction: Interaction, error: Exception) -> NoReturn:
        """Handle error raised in the context of app commands."""
        return

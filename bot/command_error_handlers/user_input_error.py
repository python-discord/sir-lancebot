from typing import NoReturn

from discord import Interaction
from discord.ext.commands import Context, UserInputError
from pydis_core.utils.error_handling.commands import AbstractCommandErrorHandler

from ._utils import create_error_embed, get_parent_command_and_subcontext, revert_cooldown_counter


class UserInputErrorHandler(AbstractCommandErrorHandler):
    """An handler for the UserInputError error."""

    async def should_handle_error(self, error: Exception) -> bool:
        """A predicate that determines whether the error should be handled or not."""
        return isinstance(error, UserInputError)

    async def handle_text_command_error(self, context: Context, error: Exception) -> NoReturn:
        """Handle error raised in the context of text commands."""
        revert_cooldown_counter(context.command, context.message)
        parent_command, ctx = get_parent_command_and_subcontext(context)
        usage = f"```\n{ctx.prefix}{parent_command}{ctx.command} {ctx.command.signature}\n```"
        embed = create_error_embed(
            f"Your input was invalid: {error}\n\nUsage:{usage}"
        )
        await context.send(embed=embed)

    async def handle_app_command_error(self, interaction: Interaction, error: Exception) -> NoReturn:
        """Handle error raised in the context of app commands."""
        raise Exception from error

from typing import NoReturn

from discord import Embed, Interaction
from discord.ext.commands import Context
from pydis_core.utils.error_handling.commands import AbstractCommandErrorHandler

from bot.constants import NEGATIVE_REPLIES
from bot.utils.exceptions import MovedCommandError

from ._utils import create_error_embed


class MovedCommandErrorHandler(AbstractCommandErrorHandler):
    """An handler for the MovedCommand error."""

    async def should_handle_error(self, error: Exception) -> bool:
        """A predicate that determines whether the error should be handled or not."""
        return isinstance(error, MovedCommandError)

    async def handle_text_command_error(self, context: Context, error: Exception) -> NoReturn:
        """Handle error raised in the context of text commands."""
        await context.send(
            embed=self._get_error_embed(context.prefix, context.command.qualified_name, error.new_command_name)
        )

    async def handle_app_command_error(self, interaction: Interaction, error: Exception) -> NoReturn:
        """Handle error raised in the context of app commands."""
        await interaction.response.send_message(
            embed=self._get_error_embed("/", interaction.command.name, error.new_command_name)
        )

    @staticmethod
    def _get_error_embed(prefix: str, command_name: str, new_command_name: str) -> Embed:
        return create_error_embed(
            message=(
                f"This command, `{prefix}{command_name}` has moved to `{new_command_name}`.\n"
                f"Please use `{new_command_name}` instead."
            ),
            title=NEGATIVE_REPLIES
        )

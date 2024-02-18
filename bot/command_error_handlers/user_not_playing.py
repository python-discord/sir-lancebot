from typing import NoReturn

from discord import Interaction
from discord.ext.commands import Context
from pydis_core.utils.error_handling.commands import AbstractCommandErrorHandler

from bot.utils.exceptions import UserNotPlayingError


class UserNotPlayingErrorHandler(AbstractCommandErrorHandler):
    """An handler for the UserNotPlayingError error."""

    async def should_handle_error(self, error: Exception) -> bool:
        """A predicate that determines whether the error should be handled or not."""
        return isinstance(error, UserNotPlayingError)

    async def handle_text_command_error(self, context: Context, error: Exception) -> NoReturn:
        """Handle error raised in the context of text commands."""
        await context.send("Game not found.")

    async def handle_app_command_error(self, interaction: Interaction, error: Exception) -> NoReturn:
        """Handle error raised in the context of app commands."""
        await interaction.response.send_message("Game not found.")

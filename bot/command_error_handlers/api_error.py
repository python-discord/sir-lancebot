from typing import NoReturn

from discord import Interaction
from discord.ext.commands import Context
from pydis_core.utils.error_handling.commands import AbstractCommandErrorHandler

from bot.constants import NEGATIVE_REPLIES
from bot.utils.exceptions import APIError

from ._utils import create_error_embed


class APIErrorHandler(AbstractCommandErrorHandler):
    """An handler for the APIError error."""

    async def should_handle_error(self, error: Exception) -> bool:
        """A predicate that determines whether the error should be handled or not."""
        return isinstance(error, APIError)

    async def handle_text_command_error(self, context: Context, error: Exception) -> NoReturn:
        """Handle error raised in the context of text commands."""
        await context.send(
            embed=create_error_embed(
                f"There was an error when communicating with the {error.api}",
                NEGATIVE_REPLIES
            )
        )

    async def handle_app_command_error(self, interaction: Interaction, error: Exception) -> NoReturn:
        """Handle error raised in the context of app commands."""
        await interaction.response.send_message(
            embed=create_error_embed(
                f"There was an error when communicating with the {error.api}",
                NEGATIVE_REPLIES
            )
        )

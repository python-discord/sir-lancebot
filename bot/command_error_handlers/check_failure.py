from typing import NoReturn

from discord import Embed, Interaction
from discord.ext.commands import CheckFailure, Context, NoPrivateMessage
from pydis_core.utils.error_handling.commands import AbstractCommandErrorHandler

from bot.constants import Channels, NEGATIVE_REPLIES
from bot.utils.decorators import InChannelCheckFailure, InMonthCheckFailure

from ._utils import create_error_embed


class CheckFailureErrorHandler(AbstractCommandErrorHandler):
    """An handler for the CheckFailure error."""

    async def should_handle_error(self, error: Exception) -> bool:
        """A predicate that determines whether the error should be handled or not."""
        return isinstance(error, CheckFailure)

    async def handle_text_command_error(self, context: Context, error: Exception) -> NoReturn:
        """Handle error raised in the context of text commands."""
        error_embed = self._get_error_embed(error)
        await context.send(embed=error_embed, delete_after=7.5)
        return

    async def handle_app_command_error(self, interaction: Interaction, error: Exception) -> NoReturn:
        """Handle error raised in the context of app commands."""
        await interaction.response.send_message(embed=self._get_error_embed(error))

    @staticmethod
    def _get_error_embed(error: Exception) -> Embed:
        if isinstance(error, InChannelCheckFailure | InMonthCheckFailure):
            return create_error_embed(str(error), NEGATIVE_REPLIES)
        if isinstance(error, NoPrivateMessage):
            return create_error_embed(
                "This command can only be used in the server. "
                f"Go to <#{Channels.sir_lancebot_playground}> instead!",
                NEGATIVE_REPLIES
            )
        return create_error_embed("You are not authorized to use this command.", NEGATIVE_REPLIES)

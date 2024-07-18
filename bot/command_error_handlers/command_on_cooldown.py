import math
from typing import NoReturn

from discord import Interaction
from discord.ext.commands import CommandOnCooldown, Context
from pydis_core.utils.error_handling.commands import AbstractCommandErrorHandler

from bot.constants import NEGATIVE_REPLIES

from ._utils import create_error_embed


class CommandOnCooldownErrorHandler(AbstractCommandErrorHandler):
    """An handler for the CommandOnCooldown error."""

    async def should_handle_error(self, error: Exception) -> bool:
        """A predicate that determines whether the error should be handled or not."""
        return isinstance(error, CommandOnCooldown)

    async def handle_text_command_error(self, context: Context, error: Exception) -> NoReturn:
        """Handle error raised in the context of text commands."""
        mins, secs = divmod(math.ceil(error.retry_after), 60)
        embed = create_error_embed(
            f"This command is on cooldown:\nPlease retry in {mins} minutes {secs} seconds.",
            NEGATIVE_REPLIES
        )
        await context.send(embed=embed, delete_after=7.5)

    async def handle_app_command_error(self, interaction: Interaction, error: Exception) -> NoReturn:
        """Handle error raised in the context of app commands."""
        raise Exception from error

from typing import NoReturn

from discord import Guild, Interaction, errors
from discord.ext.commands import Context
from pydis_core.utils.error_handling.commands import AbstractCommandErrorHandler
from pydis_core.utils.logging import get_logger
from sentry_sdk import push_scope

log = get_logger(__name__)


class DefaultCommandErrorHandler(AbstractCommandErrorHandler):
    """A default command error handler."""

    async def should_handle_error(self, error: errors.DiscordException) -> bool:
        """A predicate that determines whether the error should be handled or not."""
        return True

    async def handle_text_command_error(self, context: Context, error: errors.DiscordException) -> NoReturn:
        """Handle error raised in the context of text commands."""
        self._handle_unexpected_error(
            error=error,
            author_id=context.author.id,
            username=str(context.author),
            command_name=context.command.qualified_name,
            message_id=context.message.id,
            channel_id=context.channel.id,
            content=context.message.content,
            guild=context.guild,
            jump_url=context.message.jump_url
        )

    async def handle_app_command_error(self, interaction: Interaction, error: errors.DiscordException) -> NoReturn:
        """Handle error raised in the context of app commands."""
        self._handle_unexpected_error(
            error=error,
            author_id=interaction.user.id,
            username=str(interaction.user),
            command_name=interaction.command.name,
            message_id=interaction.message.id,
            channel_id=interaction.channel_id,
            content=interaction.message.content,
            guild=interaction.guild,
            jump_url=interaction.message.jump_url
        )

    def _handle_unexpected_error(
        self,
        error: errors.DiscordException,
        author_id: int,
        username: str,
        command_name: str,
        message_id: int,
        channel_id: int,
        content: str,
        guild: Guild | None = None,
        jump_url: str | None = None
    ) -> None:
        with push_scope() as scope:
            scope.user = {
                "id": author_id,
                "username": username
            }

            scope.set_tag("command", command_name)
            scope.set_tag("message_id", message_id)
            scope.set_tag("channel_id", channel_id)

            scope.set_extra("full_message", content)

            if guild is not None and jump_url is not None:
                scope.set_extra("jump_to", jump_url)

            log.exception(f"Unhandled command error: {error!s}", exc_info=error)

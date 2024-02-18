from typing import NoReturn

from discord import Embed, Interaction, errors
from discord.ext import commands
from pydis_core.utils.error_handling.commands import AbstractCommandErrorHandler
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.utils.commands import get_command_suggestions

log = get_logger(__name__)

DELETE_DELAY = 10
QUESTION_MARK_ICON = "https://cdn.discordapp.com/emojis/512367613339369475.png"


class CommandNotFoundErrorHandler(AbstractCommandErrorHandler):
    """A handler for all CommandNotFound exceptions."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def should_handle_error(self, error: errors.DiscordException) -> bool:
        """A predicate that determines whether the error should be handled or not."""
        return isinstance(error, commands.CommandNotFound)

    async def handle_app_command_error(self, interaction: Interaction, error: errors.DiscordException) -> NoReturn:
        """Handle error raised in the context of app commands."""
        # CommandNotFound cannot happen with app commands, so there's nothing to do here
        return

    async def handle_text_command_error(self, context: commands.Context, error: errors.DiscordException) -> NoReturn:
        """Handle error raised in the context of text commands."""
        if not context.invoked_with.startswith("."):
            await self.send_command_suggestion(context, context.invoked_with)

    async def send_command_suggestion(self, ctx: commands.Context, command_name: str) -> None:
        """Sends user similar commands if any can be found."""
        command_suggestions = []
        if similar_command_names := get_command_suggestions(list(self.bot.all_commands.keys()), command_name):
            for similar_command_name in similar_command_names:
                similar_command = self.bot.get_command(similar_command_name)

                if not similar_command:
                    continue

                log_msg = "Cancelling attempt to suggest a command due to failed checks."
                try:
                    if not await similar_command.can_run(ctx):
                        log.debug(log_msg)
                        continue
                except commands.errors.CommandError:
                    log.debug(log_msg)
                    continue

                command_suggestions.append(similar_command_name)

            misspelled_content = ctx.message.content
            e = Embed()
            e.set_author(name="Did you mean:", icon_url=QUESTION_MARK_ICON)
            e.description = "\n".join(
                misspelled_content.replace(command_name, cmd, 1) for cmd in command_suggestions
            )
            await ctx.send(embed=e, delete_after=DELETE_DELAY)

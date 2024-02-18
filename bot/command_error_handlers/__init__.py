from pydis_core.utils.error_handling.commands import CommandErrorManager

from bot.bot import Bot

from .command_not_found import CommandNotFoundErrorHandler
from .default import DefaultCommandErrorHandler


def bootstrap_command_error_manager(bot: Bot) -> CommandErrorManager:
    """Bootstraps the command error manager with all the needed error handlers."""
    default_handler = DefaultCommandErrorHandler()
    manager = CommandErrorManager(default=default_handler)
    manager.register_handler(CommandNotFoundErrorHandler(bot))
    return manager

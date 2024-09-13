from pydis_core.utils.error_handling.commands import CommandErrorManager

from bot.bot import Bot

from .api_error import APIErrorHandler
from .bad_argument import BadArgumentErrorHandler
from .check_failure import CheckFailureErrorHandler
from .command_not_found import CommandNotFoundErrorHandler
from .command_on_cooldown import CommandOnCooldownErrorHandler
from .default import DefaultCommandErrorHandler
from .disabled_command import DisabledCommandErrorHandler
from .moved_command import MovedCommandErrorHandler
from .user_input_error import UserInputErrorHandler
from .user_not_playing import UserNotPlayingErrorHandler


def bootstrap_command_error_manager(bot: Bot) -> CommandErrorManager:
    """Bootstraps the command error manager with all the needed error handlers."""
    default_handler = DefaultCommandErrorHandler()
    manager = CommandErrorManager(default=default_handler)
    manager.register_handler(CommandNotFoundErrorHandler(bot))
    manager.register_handler(MovedCommandErrorHandler())
    manager.register_handler(UserInputErrorHandler())
    manager.register_handler(APIErrorHandler())
    manager.register_handler(CommandOnCooldownErrorHandler())
    manager.register_handler(UserNotPlayingErrorHandler())
    manager.register_handler(BadArgumentErrorHandler())
    manager.register_handler(CheckFailureErrorHandler())
    manager.register_handler(DisabledCommandErrorHandler())
    return manager

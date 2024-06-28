from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.bot import Bot

log = get_logger(__name__)


class CommandErrorHandler(commands.Cog):
    """A error handler for the PythonDiscord server."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Activates when a command raises an error."""
        if getattr(error, "handled", False):
            log.debug(f"Command {ctx.command} had its error already handled locally; ignoring.")
            return

        error = getattr(error, "original", error)
        log.debug(
            f"Error Encountered: {type(error).__name__} - {error!s}, "
            f"Command: {ctx.command}, "
            f"Author: {ctx.author}, "
            f"Channel: {ctx.channel}"
        )

        await self.bot.command_error_manager.handle_error(error, ctx)


async def setup(bot: Bot) -> None:
    """Load the ErrorHandler cog."""
    await bot.add_cog(CommandErrorHandler(bot))

import logging
import math
import sys
import traceback

from discord.ext import commands

log = logging.getLogger(__name__)


class CommandErrorHandler:
    """A error handler for the PythonDiscord server!"""

    def __init__(self, bot):
        self.bot = bot

    async def on_command_error(self, ctx, error):
        """Activates when a command opens an error"""

        if hasattr(ctx.command, 'on_error'):
            return logging.debug(
                "A command error occured but "
                "the command had it's own error handler"
            )
        error = getattr(error, 'original', error)
        if isinstance(error, commands.CommandNotFound):
            return logging.debug(
                f"{ctx.author} called '{ctx.message.content}' "
                "but no command was found"
            )
        if isinstance(error, commands.UserInputError):
            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' "
                "but entered invalid input!"
            )
            return await ctx.send(
                ":no_entry: The command you specified failed to run."
                "This is because the arguments you provided were invalid."
            )
        if isinstance(error, commands.CommandOnCooldown):
            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' "
                "but they were on cooldown!"
            )
            seconds = error.retry_after
            remaining_minutes, remaining_seconds = divmod(seconds, 60)
            time_remaining = f'{int(remaining_minutes)} minutes {math.ceil(remaining_seconds)} seconds'
            return await ctx.send(
                "This command is on cooldown,"
                f" please retry in {time_remaining}."
            )
        if isinstance(error, commands.DisabledCommand):
            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' "
                "but the command was disabled!"
            )
            return await ctx.send(
                ":no_entry: This command has been disabled."
            )
        if isinstance(error, commands.NoPrivateMessage):
            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' "
                "in a private message however the command was guild only!"
            )
            return await ctx.author.send(
                ":no_entry: This command can only be used inside a server."
            )
        if isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == 'tag list':
                logging.debug(
                    f"{ctx.author} called the command '{ctx.command}' "
                    "but entered an invalid user!"
                )
                return await ctx.send(
                    "I could not find that member. Please try again."
                )
            else:
                logging.debug(
                    f"{ctx.author} called the command '{ctx.command}' "
                    "but entered a bad argument!"
                )
                return await ctx.send(
                    "The argument you provided was invalid."
                )
        if isinstance(error, commands.CheckFailure):
            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' "
                "but the checks failed!"
            )
            return await ctx.send(
                ":no_entry: You are not authorized to use this command."
            )
        print(
            f"Ignoring exception in command {ctx.command}:",
            file=sys.stderr
        )
        logging.warning(
            f"{ctx.author} called the command '{ctx.command}' "
            "however the command failed to run with the error:"
            f"-------------\n{error}"
        )
        traceback.print_exception(
            type(error),
            error,
            error.__traceback__,
            file=sys.stderr
        )


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
    log.debug("CommandErrorHandler cog loaded")

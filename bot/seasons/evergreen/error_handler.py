import logging
import math
import sys
import traceback

from discord.ext import commands

log = logging.getLogger(__name__)


class CommandErrorHandler:
    """A error handler for the PythonDiscord server."""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def revert_cooldown_counter(command, message):
        """Undoes the last cooldown counter for user-error cases."""
        if command._buckets.valid:
            bucket = command._buckets.get_bucket(message)
            bucket._tokens = min(bucket.rate, bucket._tokens + 1)
            logging.debug(
                "Cooldown counter reverted as the command was not used correctly."
            )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Activates when a command opens an error."""

        if hasattr(ctx.command, 'on_error'):
            return logging.debug(
                "A command error occured but the command had it's own error handler."
            )

        error = getattr(error, 'original', error)

        if isinstance(error, commands.CommandNotFound):
            return logging.debug(
                f"{ctx.author} called '{ctx.message.content}' but no command was found."
            )

        if isinstance(error, commands.UserInputError):
            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' but entered invalid input!"
            )

            self.revert_cooldown_counter(ctx.command, ctx.message)

            return await ctx.send(
                ":no_entry: The command you specified failed to run. "
                "This is because the arguments you provided were invalid."
            )

        if isinstance(error, commands.CommandOnCooldown):
            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' but they were on cooldown!"
            )
            remaining_minutes, remaining_seconds = divmod(error.retry_after, 60)

            return await ctx.send(
                "This command is on cooldown, please retry in "
                f"{int(remaining_minutes)} minutes {math.ceil(remaining_seconds)} seconds."
            )

        if isinstance(error, commands.DisabledCommand):
            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' but the command was disabled!"
            )
            return await ctx.send(":no_entry: This command has been disabled.")

        if isinstance(error, commands.NoPrivateMessage):
            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' "
                "in a private message however the command was guild only!"
            )
            return await ctx.author.send(":no_entry: This command can only be used in the server.")

        if isinstance(error, commands.BadArgument):
            self.revert_cooldown_counter(ctx.command, ctx.message)

            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' but entered a bad argument!"
            )
            return await ctx.send("The argument you provided was invalid.")

        if isinstance(error, commands.CheckFailure):
            logging.debug(f"{ctx.author} called the command '{ctx.command}' but the checks failed!")
            return await ctx.send(":no_entry: You are not authorized to use this command.")

        print(f"Ignoring exception in command {ctx.command}:", file=sys.stderr)

        logging.warning(
            f"{ctx.author} called the command '{ctx.command}' "
            "however the command failed to run with the error:"
            f"-------------\n{error}"
        )

        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


def setup(bot):
    """Error handler Cog load."""

    bot.add_cog(CommandErrorHandler(bot))
    log.info("CommandErrorHandler cog loaded")

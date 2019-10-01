import logging
import math
import random
import sys

from discord import Colour, Embed, Message
from discord.ext import commands

from bot.constants import NEGATIVE_REPLIES
from bot.decorators import InChannelCheckFailure

log = logging.getLogger(__name__)


class CommandErrorHandler(commands.Cog):
    """A error handler for the PythonDiscord server."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def revert_cooldown_counter(command: commands.Command, message: Message) -> None:
        """Undoes the last cooldown counter for user-error cases."""
        if command._buckets.valid:
            bucket = command._buckets.get_bucket(message)
            bucket._tokens = min(bucket.rate, bucket._tokens + 1)
            logging.debug(
                "Cooldown counter reverted as the command was not used correctly."
            )

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Activates when a command opens an error."""
        if hasattr(ctx.command, 'on_error'):
            return logging.debug(
                "A command error occured but the command had it's own error handler."
            )

        error = getattr(error, 'original', error)

        if isinstance(error, InChannelCheckFailure):
            logging.debug(
                f"{ctx.author} the command '{ctx.command}', but they did not have "
                f"permissions to run commands in the channel {ctx.channel}!"
            )
            embed = Embed(colour=Colour.red())
            embed.title = random.choice(NEGATIVE_REPLIES)
            embed.description = str(error)
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.CommandNotFound):
            return logging.debug(
                f"{ctx.author} called '{ctx.message.content}' but no command was found."
            )

        if isinstance(error, commands.UserInputError):
            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' but entered invalid input!"
            )

            self.revert_cooldown_counter(ctx.command, ctx.message)

            log.exception(type(error).__name__, exc_info=error)

            await ctx.send(
                ":no_entry: The command you specified failed to run. "
                "This is because the arguments you provided were invalid."
            )
            return

        if isinstance(error, commands.CommandOnCooldown):
            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' but they were on cooldown!"
            )
            remaining_minutes, remaining_seconds = divmod(error.retry_after, 60)

            await ctx.send(
                "This command is on cooldown, please retry in "
                f"{int(remaining_minutes)} minutes {math.ceil(remaining_seconds)} seconds."
            )
            return

        if isinstance(error, commands.DisabledCommand):
            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' but the command was disabled!"
            )
            await ctx.send(":no_entry: This command has been disabled.")
            return

        if isinstance(error, commands.NoPrivateMessage):
            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' "
                "in a private message however the command was guild only!"
            )
            await ctx.author.send(":no_entry: This command can only be used in the server.")
            return

        if isinstance(error, commands.BadArgument):
            self.revert_cooldown_counter(ctx.command, ctx.message)

            logging.debug(
                f"{ctx.author} called the command '{ctx.command}' but entered a bad argument!"
            )
            await ctx.send("The argument you provided was invalid.")
            return

        if isinstance(error, commands.CheckFailure):
            logging.debug(f"{ctx.author} called the command '{ctx.command}' but the checks failed!")
            await ctx.send(":no_entry: You are not authorized to use this command.")
            return

        print(f"Ignoring exception in command {ctx.command}:", file=sys.stderr)

        logging.warning(
            f"{ctx.author} called the command '{ctx.command}' "
            f"however the command failed to run with the error: {error}"
        )

        log.exception(type(error).__name__, exc_info=error)


def setup(bot: commands.Bot) -> None:
    """Error handler Cog load."""
    bot.add_cog(CommandErrorHandler(bot))
    log.info("CommandErrorHandler cog loaded")

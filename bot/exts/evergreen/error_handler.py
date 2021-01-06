import logging
import math
import random
from typing import Iterable, Union

from discord import Embed, Message
from discord.ext import commands
from sentry_sdk import push_scope

from bot.constants import Colours, ERROR_REPLIES, NEGATIVE_REPLIES
from bot.utils.decorators import InChannelCheckFailure, InMonthCheckFailure
from bot.utils.exceptions import UserNotPlayingError

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
            logging.debug("Cooldown counter reverted as the command was not used correctly.")

    @staticmethod
    def error_embed(message: str, title: Union[Iterable, str] = ERROR_REPLIES) -> Embed:
        """Build a basic embed with red colour and either a random error title or a title provided."""
        embed = Embed(colour=Colours.soft_red)
        if isinstance(title, str):
            embed.title = title
        else:
            embed.title = random.choice(title)
        embed.description = message
        return embed

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Activates when a command opens an error."""
        if getattr(error, 'handled', False):
            logging.debug(f"Command {ctx.command} had its error already handled locally; ignoring.")
            return

        error = getattr(error, 'original', error)
        logging.debug(
            f"Error Encountered: {type(error).__name__} - {str(error)}, "
            f"Command: {ctx.command}, "
            f"Author: {ctx.author}, "
            f"Channel: {ctx.channel}"
        )

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, (InChannelCheckFailure, InMonthCheckFailure)):
            await ctx.send(embed=self.error_embed(str(error), NEGATIVE_REPLIES), delete_after=7.5)
            return

        if isinstance(error, commands.UserInputError):
            self.revert_cooldown_counter(ctx.command, ctx.message)
            embed = self.error_embed(
                f"Your input was invalid: {error}\n\nUsage:\n```{ctx.prefix}{ctx.command} {ctx.command.signature}```"
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.CommandOnCooldown):
            mins, secs = divmod(math.ceil(error.retry_after), 60)
            embed = self.error_embed(
                f"This command is on cooldown:\nPlease retry in {mins} minutes {secs} seconds.",
                NEGATIVE_REPLIES
            )
            await ctx.send(embed=embed, delete_after=7.5)
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send(embed=self.error_embed("This command has been disabled.", NEGATIVE_REPLIES))
            return

        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send(embed=self.error_embed("This command can only be used in the server.", NEGATIVE_REPLIES))
            return

        if isinstance(error, commands.BadArgument):
            self.revert_cooldown_counter(ctx.command, ctx.message)
            embed = self.error_embed(
                "The argument you provided was invalid: "
                f"{error}\n\nUsage:\n```{ctx.prefix}{ctx.command} {ctx.command.signature}```"
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.CheckFailure):
            await ctx.send(embed=self.error_embed("You are not authorized to use this command.", NEGATIVE_REPLIES))
            return

        if isinstance(error, UserNotPlayingError):
            await ctx.send("Game not found.")
            return

        with push_scope() as scope:
            scope.user = {
                "id": ctx.author.id,
                "username": str(ctx.author)
            }

            scope.set_tag("command", ctx.command.qualified_name)
            scope.set_tag("message_id", ctx.message.id)
            scope.set_tag("channel_id", ctx.channel.id)

            scope.set_extra("full_message", ctx.message.content)

            if ctx.guild is not None:
                scope.set_extra(
                    "jump_to",
                    f"https://discordapp.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id}"
                )

            log.exception(f"Unhandled command error: {str(error)}", exc_info=error)


def setup(bot: commands.Bot) -> None:
    """Error handler Cog load."""
    bot.add_cog(CommandErrorHandler(bot))

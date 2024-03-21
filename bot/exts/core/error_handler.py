import math
import random
from collections.abc import Iterable

from discord import Embed, Message
from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import Channels, Colours, ERROR_REPLIES, NEGATIVE_REPLIES
from bot.utils.decorators import InChannelCheckFailure, InMonthCheckFailure
from bot.utils.exceptions import APIError, UserNotPlayingError

log = get_logger(__name__)


DELETE_DELAY = 10
QUESTION_MARK_ICON = "https://cdn.discordapp.com/emojis/512367613339369475.png"


class CommandErrorHandler(commands.Cog):
    """A error handler for the PythonDiscord server."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def revert_cooldown_counter(command: commands.Command, message: Message) -> None:
        """Undoes the last cooldown counter for user-error cases."""
        if command._buckets.valid:
            bucket = command._buckets.get_bucket(message)
            bucket._tokens = min(bucket.rate, bucket._tokens + 1)
            log.debug("Cooldown counter reverted as the command was not used correctly.")

    @staticmethod
    def error_embed(message: str, title: Iterable | str = ERROR_REPLIES) -> Embed:
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
        """Activates when a command raises an error."""
        if getattr(error, "handled", False):
            log.debug(f"Command {ctx.command} had its error already handled locally; ignoring.")
            return

        parent_command = ""
        if subctx := getattr(ctx, "subcontext", None):
            parent_command = f"{ctx.command} "
            ctx = subctx

        error = getattr(error, "original", error)
        log.debug(
            f"Error Encountered: {type(error).__name__} - {error!s}, "
            f"Command: {ctx.command}, "
            f"Author: {ctx.author}, "
            f"Channel: {ctx.channel}"
        )

        if isinstance(error, InChannelCheckFailure | InMonthCheckFailure):
            await ctx.send(embed=self.error_embed(str(error), NEGATIVE_REPLIES), delete_after=7.5)
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
            await ctx.send(
                embed=self.error_embed(
                    "This command can only be used in the server. "
                    f"Go to <#{Channels.sir_lancebot_playground}> instead!",
                    NEGATIVE_REPLIES
                )
            )
            return

        if isinstance(error, commands.BadArgument):
            self.revert_cooldown_counter(ctx.command, ctx.message)
            embed = self.error_embed(
                "The argument you provided was invalid: "
                f"{error}\n\nUsage:\n```\n{ctx.prefix}{parent_command}{ctx.command} {ctx.command.signature}\n```"
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.CheckFailure):
            await ctx.send(embed=self.error_embed("You are not authorized to use this command.", NEGATIVE_REPLIES))
            return

        if isinstance(error, UserNotPlayingError):
            await ctx.send("Game not found.")
            return

        if isinstance(error, APIError):
            await ctx.send(
                embed=self.error_embed(
                    f"There was an error when communicating with the {error.api}",
                    NEGATIVE_REPLIES
                )
            )
            return

        await self.bot.command_error_manager.handle_error(error, ctx)


async def setup(bot: Bot) -> None:
    """Load the ErrorHandler cog."""
    await bot.add_cog(CommandErrorHandler(bot))

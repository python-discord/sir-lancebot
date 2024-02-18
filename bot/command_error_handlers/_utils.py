import random
from collections.abc import Iterable

from discord import Embed, Message
from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.constants import Colours, ERROR_REPLIES

log = get_logger(__name__)


def create_error_embed(message: str, title: Iterable | str = ERROR_REPLIES) -> Embed:
    """Build a basic embed with red colour and either a random error title or a title provided."""
    embed = Embed(colour=Colours.soft_red)
    if isinstance(title, str):
        embed.title = title
    else:
        embed.title = random.choice(title)
    embed.description = message
    return embed


def revert_cooldown_counter(command: commands.Command, message: Message) -> None:
    """Undoes the last cooldown counter for user-error cases."""
    if command._buckets.valid:
        bucket = command._buckets.get_bucket(message)
        bucket._tokens = min(bucket.rate, bucket._tokens + 1)
        log.debug("Cooldown counter reverted as the command was not used correctly.")


def get_parent_command_and_subcontext(context: commands.Context) -> tuple[str, commands.Context]:
    """Extracts the parent command and subcontext, if any."""
    parent_command = ""
    ctx = context
    if sub_context := getattr(context, "subcontext", None):
        parent_command = f"{context.command} "
        ctx = sub_context

    return parent_command, ctx

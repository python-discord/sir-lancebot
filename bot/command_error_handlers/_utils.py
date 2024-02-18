import random
from collections.abc import Iterable

from discord import Embed

from bot.constants import Colours, ERROR_REPLIES


def create_error_embed(message: str, title: Iterable | str = ERROR_REPLIES) -> Embed:
    """Build a basic embed with red colour and either a random error title or a title provided."""
    embed = Embed(colour=Colours.soft_red)
    if isinstance(title, str):
        embed.title = title
    else:
        embed.title = random.choice(title)
    embed.description = message
    return embed

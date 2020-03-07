import logging
import pkgutil
from pathlib import Path
from typing import List

from bot.seasons.season import SeasonBase

__all__ = ("SeasonBase", "get_seasons", "get_extensions")

log = logging.getLogger(__name__)


def get_seasons() -> List[str]:
    """Returns all the Season objects located in /bot/seasons/."""
    seasons = []

    for module in pkgutil.iter_modules([Path("bot/seasons")]):
        if module.ispkg:
            seasons.append(module.name)
    return seasons


def get_extensions() -> List[str]:
    """
    Give a list of dot-separated paths to all extensions.

    The strings are formatted in a way such that the bot's `load_extension`
    method can take them. Use this to load all available extensions.
    """
    base_path = Path("bot", "seasons")
    extensions = []

    for package in pkgutil.iter_modules([base_path]):
        package_path = base_path.joinpath(package.name)

        for module in pkgutil.iter_modules([package_path]):
            extensions.append(f"bot.seasons.{package.name}.{module.name}")

    return extensions

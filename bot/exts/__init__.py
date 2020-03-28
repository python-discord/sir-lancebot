import logging
import pkgutil
from pathlib import Path
from typing import List

__all__ = ("get_package_names", "get_extensions")

log = logging.getLogger(__name__)


def get_package_names() -> List[str]:
    """Return names of all packages located in /bot/exts/."""
    seasons = [
        package.name
        for package in pkgutil.iter_modules(__path__)
        if package.ispkg
    ]

    return seasons


def get_extensions() -> List[str]:
    """
    Give a list of dot-separated paths to all extensions.

    The strings are formatted in a way such that the bot's `load_extension`
    method can take them. Use this to load all available extensions.
    """
    base_path = Path(__path__[0])
    extensions = []

    for season in get_package_names():
        for module in pkgutil.iter_modules([base_path.joinpath(season)]):
            extensions.append(f"bot.exts.{season}.{module.name}")

    return extensions

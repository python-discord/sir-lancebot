import logging
import pkgutil
from pathlib import Path
from typing import List, Optional, Tuple

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

        if package.ispkg:
            package_path = base_path.joinpath(package.name)

            for module in pkgutil.iter_modules([package_path]):
                extensions.append(f"bot.seasons.{package.name}.{module.name}")
        else:
            extensions.append(f"bot.seasons.{package.name}")

    return extensions


class SeasonBase:
    """Base for Seasonal classes."""

    name: Optional[str] = "evergreen"
    bot_name: str = "SeasonalBot"

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    should_announce: bool = False

    colour: Optional[int] = None
    icon: Tuple[str, ...] = ("/logos/logo_full/logo_full.png",)
    bot_icon: Optional[str] = None

    date_format: str = "%d/%m/%Y"

    index: int = 0

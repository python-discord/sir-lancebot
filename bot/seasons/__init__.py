import logging
import pkgutil
from datetime import datetime
from pathlib import Path
from typing import List, Set, Type

from bot.constants import Month

__all__ = ("SeasonBase", "get_seasons", "get_extensions", "get_current_season")

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
    """
    Base for Seasonal classes.

    This serves as the off-season fallback for when no specific
    seasons are active.

    Seasons are 'registered' by simply by inheriting from `SeasonBase`,
    as they are then found by looking at `__subclasses__`.
    """

    season_name: str = "Evergreen"
    bot_name: str = "SeasonalBot"

    description: str = "The default season!"

    branding_path: str = "seasonal/evergreen"

    months: Set[Month] = set(Month)


def get_current_season() -> Type[SeasonBase]:
    """Give active season, based on current UTC month."""
    current_month = Month(datetime.utcnow().month)

    active_seasons = tuple(
        season
        for season in SeasonBase.__subclasses__()
        if current_month in season.months
    )

    if not active_seasons:
        return SeasonBase

    if len(active_seasons) > 1:
        log.warning(f"Multiple active season in month {current_month.name}")

    return active_seasons[0]

import logging
import pkgutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set, Type

from bot.constants import Colours, Month

__all__ = (
    "SeasonBase",
    "Christmas",
    "Easter",
    "Halloween",
    "Pride",
    "Valentines",
    "Wildcard",
    "get_season_names",
    "get_extensions",
    "get_current_season",
    "get_season",
)

log = logging.getLogger(__name__)


class SeasonBase:
    """
    Base for Seasonal classes.

    This serves as the off-season fallback for when no specific
    seasons are active.

    Seasons are 'registered' simply by inheriting from `SeasonBase`.
    We discover them by calling `__subclasses__`.
    """

    season_name: str = "Evergreen"
    bot_name: str = "SeasonalBot"

    colour: str = Colours.soft_green
    description: str = "The default season!"

    branding_path: str = "seasonal/evergreen"

    months: Set[Month] = set(Month)


class Christmas(SeasonBase):
    """Branding for december."""

    season_name = "Festive season"
    bot_name = "Merrybot"

    colour = Colours.soft_red
    description = (
        "The time is here to get into the festive spirit! No matter who you are, where you are, "
        "or what beliefs you may follow, we hope every one of you enjoy this festive season!"
    )

    branding_path = "seasonal/christmas"

    months = {Month.december}


class Easter(SeasonBase):
    """Branding for april."""

    season_name = "Easter"
    bot_name = "BunnyBot"

    colour = Colours.bright_green
    description = (
        "Bunny here, bunny there, bunny everywhere! Here at Python Discord, we celebrate "
        "our version of Easter during the entire month of April."
    )

    branding_path = "seasonal/easter"

    months = {Month.april}


class Halloween(SeasonBase):
    """Branding for october."""

    season_name = "Halloween"
    bot_name = "NeonBot"

    colour = Colours.orange
    description = "Trick or treat?!"

    branding_path = "seasonal/halloween"

    months = {Month.october}


class Pride(SeasonBase):
    """Branding for june."""

    season_name = "Pride"
    bot_name = "ProudBot"

    colour = Colours.pink
    description = (
        "The month of June is a special month for us at Python Discord. It is very important to us "
        "that everyone feels welcome here, no matter their origin, identity or sexuality. During the "
        "month of June, while some of you are participating in Pride festivals across the world, "
        "we will be celebrating individuality and commemorating the history and challenges "
        "of the LGBTQ+ community with a Pride event of our own!"
    )

    branding_path = "seasonal/pride"

    months = {Month.june}


class Valentines(SeasonBase):
    """Branding for february."""

    season_name = "Valentines"
    bot_name = "TenderBot"

    colour = Colours.pink
    description = "Love is in the air!"

    branding_path = "seasonal/valentines"

    months = {Month.february}


class Wildcard(SeasonBase):
    """Branding for august."""

    season_name = "Wildcard"
    bot_name = "RetroBot"

    colour = Colours.purple
    description = "A season full of surprises!"

    months = {Month.august}


def get_season_names() -> List[str]:
    """Return names of all packages located in /bot/seasons/."""
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

    for season in get_season_names():
        for module in pkgutil.iter_modules([base_path.joinpath(season)]):
            extensions.append(f"bot.seasons.{season}.{module.name}")

    return extensions


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


def get_season(name: str) -> Optional[Type[SeasonBase]]:
    """
    Give season such that its class name or its `season_name` attr match `name` (caseless).

    If no such season exists, return None.
    """
    name = name.casefold()

    for season in [SeasonBase] + SeasonBase.__subclasses__():
        matches = (season.__name__.casefold(), season.season_name.casefold())

        if name in matches:
            return season

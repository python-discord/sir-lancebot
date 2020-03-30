import logging
import typing as t

from bot.constants import Colours, Month
from bot.utils import resolve_current_month

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

    months: t.Set[Month] = set(Month)


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


def get_all_seasons() -> t.List[t.Type[SeasonBase]]:
    """Give all available season classes."""
    return [SeasonBase] + SeasonBase.__subclasses__()


def get_current_season() -> t.Type[SeasonBase]:
    """Give active season, based on current UTC month."""
    current_month = resolve_current_month()

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


def get_season(name: str) -> t.Optional[t.Type[SeasonBase]]:
    """
    Give season such that its class name or its `season_name` attr match `name` (caseless).

    If no such season exists, return None.
    """
    name = name.casefold()

    for season in get_all_seasons():
        matches = (season.__name__.casefold(), season.season_name.casefold())

        if name in matches:
            return season

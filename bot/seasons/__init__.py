import datetime

from .christmas import Christmas
from .evergreen import Evergreen
from .halloween import Halloween
from .season import Season

__all__ = (
    "Christmas",
    "Halloween",
    "Season",
    "get_season"
)

SEASONS = {
    "halloween": Halloween,
    "christmas": Christmas
}


def get_season(bot, season_name: str = None, date: datetime.date = None):
    """
    Returns a Season object based on either a string or a date.
    """

    assert season_name or date, "This function requires either a season or a date in order to run."

    # If there's a season name, we can just grab the correct class.
    if season_name:
        season_name = season_name.lower()
        if season_name not in SEASONS:
            return Evergreen(bot)
        return SEASONS[season_name](bot)

    # If not, we have to figure out if the date matches any of the seasons.
    for season_object in SEASONS.values():
        season_object = season_object(bot)
        if season_object.start <= date <= season_object.end:
            return season_object

    # Nothing matches!
    return Evergreen(bot)

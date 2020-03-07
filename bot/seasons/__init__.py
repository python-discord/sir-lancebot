import logging
import pkgutil
from pathlib import Path
from typing import List

from bot.seasons.season import SeasonBase

__all__ = ("SeasonBase", "get_seasons")

log = logging.getLogger(__name__)


def get_seasons() -> List[str]:
    """Returns all the Season objects located in /bot/seasons/."""
    seasons = []

    for module in pkgutil.iter_modules([Path("bot/seasons")]):
        if module.ispkg:
            seasons.append(module.name)
    return seasons

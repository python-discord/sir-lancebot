import contextlib
import datetime
import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import List, Optional, Tuple, Type, Union

import discord
from discord.ext import commands

from bot.bot import bot
from bot.constants import Channels, Client, Roles
from bot.decorators import with_role

log = logging.getLogger(__name__)

ICON_BASE_URL = "https://raw.githubusercontent.com/python-discord/branding/master"


def get_seasons() -> List[str]:
    """Returns all the Season objects located in /bot/seasons/."""
    seasons = []

    for module in pkgutil.iter_modules([Path("bot/seasons")]):
        if module.ispkg:
            seasons.append(module.name)
    return seasons


def get_season_class(season_name: str) -> Type["SeasonBase"]:
    """Gets the season class of the season module."""
    season_lib = importlib.import_module(f"bot.seasons.{season_name}")
    class_name = season_name.replace("_", " ").title().replace(" ", "")
    return getattr(season_lib, class_name)


class SeasonBase:
    """Base class for Seasonal classes."""

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

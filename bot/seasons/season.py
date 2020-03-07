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

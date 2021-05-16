try:
    from dotenv import load_dotenv
    print("Found .env file, loading environment variables from it.")
    load_dotenv(override=True)
except ModuleNotFoundError:
    pass

import asyncio
import logging
import logging.handlers
import os
from functools import partial, partialmethod
from pathlib import Path

import arrow
from discord.ext import commands

from bot.command import Command
from bot.constants import Client
from bot.group import Group


# Configure the "TRACE" logging level (e.g. "log.trace(message)")
logging.TRACE = 5
logging.addLevelName(logging.TRACE, "TRACE")


def monkeypatch_trace(self: logging.Logger, msg: str, *args, **kwargs) -> None:
    """
    Log 'msg % args' with severity 'TRACE'.

    To pass exception information, use the keyword argument exc_info with a true value, e.g.
    logger.trace("Houston, we have an %s", "interesting problem", exc_info=1)
    """
    if self.isEnabledFor(logging.TRACE):
        self._log(logging.TRACE, msg, args, **kwargs)


logging.Logger.trace = monkeypatch_trace

# Set timestamp of when execution started (approximately)
start_time = arrow.utcnow()

# Set up file logging
log_dir = Path("bot/log")
log_file = log_dir / "hackbot.log"
os.makedirs(log_dir, exist_ok=True)

# File handler rotates logs every 5 MB
file_handler = logging.handlers.RotatingFileHandler(
    log_file, maxBytes=5 * (2**20), backupCount=10, encoding="utf-8",
)
file_handler.setLevel(logging.TRACE if Client.debug else logging.DEBUG)

# Console handler prints to terminal
console_handler = logging.StreamHandler()
level = logging.TRACE if Client.debug else logging.INFO
console_handler.setLevel(level)

# Remove old loggers, if any
root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)

# Silence irrelevant loggers
logging.getLogger("discord").setLevel(logging.ERROR)
logging.getLogger("websockets").setLevel(logging.ERROR)
logging.getLogger("PIL").setLevel(logging.ERROR)
logging.getLogger("matplotlib").setLevel(logging.ERROR)

# Setup new logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s %(levelname)s: %(message)s",
    datefmt="%D %H:%M:%S",
    level=logging.TRACE if Client.debug else logging.DEBUG,
    handlers=[console_handler, file_handler],
)
logging.getLogger().info("Logging initialization complete")


# On Windows, the selector event loop is required for aiodns.
if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# Monkey-patch discord.py decorators to use the both the Command and Group subclasses which supports root aliases.
# Must be patched before any cogs are added.
commands.command = partial(commands.command, cls=Command)
commands.GroupMixin.command = partialmethod(commands.GroupMixin.command, cls=Command)

commands.group = partial(commands.group, cls=Group)
commands.GroupMixin.group = partialmethod(commands.GroupMixin.group, cls=Group)

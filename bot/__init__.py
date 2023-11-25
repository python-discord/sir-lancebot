try:
    from dotenv import load_dotenv
    print("Found .env file, loading environment variables from it.")  # noqa: T201
    load_dotenv(override=True)
except ModuleNotFoundError:
    pass

import asyncio
import os
from typing import TYPE_CHECKING

import arrow
from pydis_core.utils import apply_monkey_patches

from bot import log

if TYPE_CHECKING:
    from bot.bot import Bot

log.setup()

# Set timestamp of when execution started (approximately)
start_time = arrow.utcnow()

# On Windows, the selector event loop is required for aiodns.
if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

apply_monkey_patches()

instance: "Bot" = None  # Global Bot instance.

try:
    from dotenv import load_dotenv
    print("Found .env file, loading environment variables from it.")  # noqa: T201
    load_dotenv(override=True)
except ModuleNotFoundError:
    pass

import asyncio
import logging
import os
from typing import TYPE_CHECKING

import arrow
import sentry_sdk
from pydis_core.utils import apply_monkey_patches
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from bot import log

if TYPE_CHECKING:
    from bot.bot import Bot

sentry_logging = LoggingIntegration(
    level=logging.DEBUG,
    event_level=logging.WARNING
)

sentry_sdk.init(
    dsn=os.environ.get("BOT_SENTRY_DSN"),
    integrations=[
        sentry_logging,
        RedisIntegration()
    ],
    release=f"sir-lancebot@{os.environ.get('GIT_SHA', 'foobar')}"
)

log.setup()

# Set timestamp of when execution started (approximately)
start_time = arrow.utcnow()

# On Windows, the selector event loop is required for aiodns.
if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

apply_monkey_patches()

instance: "Bot" = None  # Global Bot instance.

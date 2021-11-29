try:
    from dotenv import load_dotenv
    print("Found .env file, loading environment variables from it.")
    load_dotenv(override=True)
except ModuleNotFoundError:
    pass

import asyncio
import logging
import os
from functools import partial, partialmethod

import arrow
import sentry_sdk
from discord.ext import commands
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from bot import log, monkey_patches

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

monkey_patches.patch_typing()

# Monkey-patch discord.py decorators to use the both the Command and Group subclasses which supports root aliases.
# Must be patched before any cogs are added.
commands.command = partial(commands.command, cls=monkey_patches.Command)
commands.GroupMixin.command = partialmethod(commands.GroupMixin.command, cls=monkey_patches.Command)

commands.group = partial(commands.group, cls=monkey_patches.Group)
commands.GroupMixin.group = partialmethod(commands.GroupMixin.group, cls=monkey_patches.Group)

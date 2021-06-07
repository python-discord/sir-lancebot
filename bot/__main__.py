import asyncio
import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from bot.bot import bot
from bot.constants import Client, GIT_SHA, STAFF_ROLES, WHITELISTED_CHANNELS
from bot.utils.decorators import whitelist_check
from bot.utils.extensions import walk_extensions

sentry_logging = LoggingIntegration(
    level=logging.DEBUG,
    event_level=logging.WARNING
)

sentry_sdk.init(
    dsn=Client.sentry_dsn,
    integrations=[
        sentry_logging,
        RedisIntegration()
    ],
    release=f"sir-lancebot@{GIT_SHA}"
)

log = logging.getLogger(__name__)

bot.add_check(whitelist_check(channels=WHITELISTED_CHANNELS, roles=STAFF_ROLES))


async def load_extensions() -> None:
    """Async wrapper to load all the extensions."""
    await bot.unloads_cache.set("bot.exts.evergreen.catify", "https://dummy-msg-link.com")
    await bot.unloads_cache.set("bot.exts.evergreen.xkd", "https://dummy-msg-link.com")

    for ext in walk_extensions():
        await bot.load_extension(ext)

loop = asyncio.get_event_loop()
loop.run_until_complete(load_extensions())

bot.run(Client.token)

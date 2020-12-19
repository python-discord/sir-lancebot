import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from bot.bot import bot
from bot.constants import Client, GIT_SHA, STAFF_ROLES, WHITELISTED_CHANNELS
from bot.utils.decorators import in_channel_check
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
    release=f"pydis-sir-lancebot@{GIT_SHA}"
)

log = logging.getLogger(__name__)

bot.add_check(in_channel_check(*WHITELISTED_CHANNELS, bypass_roles=STAFF_ROLES))

for ext in walk_extensions():
    bot.load_extension(ext)

bot.run(Client.token)

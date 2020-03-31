import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from bot.bot import bot
from bot.constants import Client, STAFF_ROLES, WHITELISTED_CHANNELS
from bot.decorators import in_channel_check

sentry_logging = LoggingIntegration(
    level=logging.DEBUG,
    event_level=logging.WARNING
)

sentry_sdk.init(
    dsn=Client.sentry_dsn,
    integrations=[sentry_logging]
)

log = logging.getLogger(__name__)

bot.add_check(in_channel_check(*WHITELISTED_CHANNELS, bypass_roles=STAFF_ROLES))
bot.load_extension("bot.help")
bot.load_extension("bot.seasons")
bot.run(Client.token)

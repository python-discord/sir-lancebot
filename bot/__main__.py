import logging

from bot.bot import bot
from bot.constants import Client, STAFF_ROLES, WHITELISTED_CHANNELS
from bot.utils.decorators import whitelist_check
from bot.utils.extensions import walk_extensions

log = logging.getLogger(__name__)

bot.add_check(whitelist_check(channels=WHITELISTED_CHANNELS, roles=STAFF_ROLES))

for ext in walk_extensions():
    bot.load_extension(ext)

if not Client.in_ci:
    bot.run(Client.token)

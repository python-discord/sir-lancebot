import logging

from bot.bot import bot
from bot.constants import Client, STAFF_ROLES, WHITELISTED_CHANNELS
from bot.seasons import get_extensions
from bot.utils.decorators import in_channel_check

log = logging.getLogger(__name__)

bot.add_check(in_channel_check(*WHITELISTED_CHANNELS, bypass_roles=STAFF_ROLES))

for ext in get_extensions():
    bot.load_extension(ext)

bot.load_extension("bot.branding")
bot.load_extension("bot.help")

bot.run(Client.token)

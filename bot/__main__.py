import logging

from bot.bot import bot
from bot.constants import Client, STAFF_ROLES, WHITELISTED_CHANNELS
from bot.decorators import in_channel_check

log = logging.getLogger(__name__)

bot.add_check(in_channel_check(*WHITELISTED_CHANNELS, bypass_roles=STAFF_ROLES))
bot.load_extension("bot.help")
bot.load_extension("bot.seasons")
bot.run(Client.token)

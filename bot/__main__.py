import logging

from bot.bot import bot
from bot.constants import Client

log = logging.getLogger(__name__)

bot.load_extension("bot.seasons")
bot.run(Client.token)

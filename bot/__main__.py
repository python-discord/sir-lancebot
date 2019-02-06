import logging

from bot.constants import Client, bot

log = logging.getLogger(__name__)

bot.load_extension("bot.seasons")
bot.run(Client.token)

import logging

from bot.constants import TOKEN, bot

log = logging.getLogger(__name__)

bot.load_extension("bot.seasons")
bot.run(TOKEN)

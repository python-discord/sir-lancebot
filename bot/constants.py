import logging
from os import environ

from bot.bot import SeasonalBot

__all__ = ('PYTHON_GUILD', 'PREFIX', 'TOKEN', 'bot')

log = logging.getLogger(__name__)

PYTHON_GUILD = int(environ.get('SEASONALBOT_GUILD', 267624335836053506))

# client constants

PREFIX = "."
TOKEN = environ.get('SEASONALBOT_TOKEN')
if TOKEN:
    token_dl = len(TOKEN) // 8
    log.info(f'Bot token loaded: {TOKEN[:token_dl]}...{TOKEN[-token_dl:]}')
else:
    log.error(f'Bot token not found: {TOKEN}')

bot = SeasonalBot(command_prefix=".")

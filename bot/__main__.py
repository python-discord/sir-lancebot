import logging
from os import environ

from discord.ext import commands

log = logging.getLogger()

# Load the token
SEASONALBOT_TOKEN = environ.get('SEASONALBOT_TOKEN')
if SEASONALBOT_TOKEN:
    token_dl = len(SEASONALBOT_TOKEN) // 8
    log.info(f'Bot token loaded: {SEASONALBOT_TOKEN[:token_dl]}...{SEASONALBOT_TOKEN[-token_dl:]}')
else:
    log.error(f'Bot token not found: {SEASONALBOT_TOKEN}')

# Create the bot
bot = commands.Bot(command_prefix=".")
bot.load_extension("bot.cogs.season")
bot.run(SEASONALBOT_TOKEN)

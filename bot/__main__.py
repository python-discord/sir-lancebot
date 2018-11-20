import logging
from os import environ
from pathlib import Path
from traceback import format_exc

from discord.ext import commands

SEASONALBOT_TOKEN = environ.get('SEASONALBOT_TOKEN')
log = logging.getLogger()

if SEASONALBOT_TOKEN:
    token_dl = len(SEASONALBOT_TOKEN) // 8
    log.info(f'Bot token loaded: {SEASONALBOT_TOKEN[:token_dl]}...{SEASONALBOT_TOKEN[-token_dl:]}')
else:
    log.error(f'Bot token not found: {SEASONALBOT_TOKEN}')

ghost_unicode = "\N{GHOST}"
bot = commands.Bot(command_prefix=commands.when_mentioned_or(".", f"{ghost_unicode} ", ghost_unicode))

log.info('Start loading extensions from ./bot/cogs/evergreen/')


if __name__ == '__main__':
    # Scan for files in the /cogs/ directory and make a list of the file names.
    cogs = [file.stem for file in Path('bot', 'cogs', 'halloween').glob('*.py') if not file.stem.startswith("__")]
    for extension in cogs:
        try:
            bot.load_extension(f'bot.cogs.halloween.{extension}')
            log.info(f'Successfully loaded extension: {extension}')
        except Exception as e:
            log.error(f'Failed to load extension {extension}: {repr(e)} {format_exc()}')

bot.run(SEASONALBOT_TOKEN)

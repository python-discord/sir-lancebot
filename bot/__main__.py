import logging
from os import environ
from pathlib import Path
from traceback import format_exc

from discord.ext import commands

HACKTOBERBOT_TOKEN = environ.get('HACKTOBERBOT_TOKEN')
log = logging.getLogger()

if HACKTOBERBOT_TOKEN:
    token_dl = len(HACKTOBERBOT_TOKEN) // 8
    log.info(f'Bot token loaded: {HACKTOBERBOT_TOKEN[:token_dl]}...{HACKTOBERBOT_TOKEN[-token_dl:]}')
else:
    log.error(f'Bot token not found: {HACKTOBERBOT_TOKEN}')

ghost_unicode = "\N{GHOST}"
bot = commands.Bot(command_prefix=commands.when_mentioned_or(".", f"{ghost_unicode} ", ghost_unicode))

log.info('Start loading extensions from ./bot/cogs/')


if __name__ == '__main__':
    # Scan for files in the /cogs/ directory and make a list of the file names.
    cogs = [file.stem for file in Path('bot', 'cogs').glob('*.py')]
    for extension in cogs:
        try:
            bot.load_extension(f'bot.cogs.{extension}')
            log.info(f'Successfully loaded extension: {extension}')
        except Exception as e:
            log.error(f'Failed to load extension {extension}: {repr(e)} {format_exc()}')
            # print(f'Failed to load extension {extension}.', file=stderr)
            # print_exc()

log.info(f'Spooky Launch Sequence Initiated...')

bot.run(HACKTOBERBOT_TOKEN)

log.info(f'HackBot has been slain!')

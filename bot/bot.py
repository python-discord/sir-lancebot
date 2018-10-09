from os import environ
from pathlib import Path
from sys import stderr
from traceback import print_exc, format_exc

from discord.ext import commands
import logging

HACKTOBERBOT_TOKEN = environ.get('HACKTOBERBOT_TOKEN')

if HACKTOBERBOT_TOKEN:
    token_dl = len(HACKTOBERBOT_TOKEN) // 8
    logging.info(f'Bot token loaded: {HACKTOBERBOT_TOKEN[:token_dl]}...{HACKTOBERBOT_TOKEN[-token_dl:]}')
else:
    logging.error(f'Bot token not found: {HACKTOBERBOT_TOKEN}')

ghost_unicode = "\N{GHOST}"
bot = commands.Bot(command_prefix=commands.when_mentioned_or(".", f"{ghost_unicode} ", ghost_unicode))

logging.info('Start loading extensions from ./cogs/')


if __name__ == '__main__':
    # Scan for files in the /cogs/ directory and make a list of the file names.
    cogs = [file.stem for file in Path('cogs').glob('*.py')]
    for extension in cogs:
        try:
            bot.load_extension(f'cogs.{extension}')
            logging.info(f'Successfully loaded extension: {extension}')
        except Exception as e:
            logging.error(f'Failed to load extension {extension}: {repr(e)} {format_exc()}')
            # print(f'Failed to load extension {extension}.', file=stderr)
            # print_exc()

logging.info(f'Spooky Launch Sequence Initiated...')

bot.run(HACKTOBERBOT_TOKEN)

logging.info(f'HackBot has been slain!')
from os import environ
from pathlib import Path
from sys import stderr
from traceback import print_exc

from discord.ext import commands

HACKTOBERBOT_TOKEN = environ.get('HACKTOBERBOT_TOKEN')

ghost_unicode = u"\U0001F47B"
bot = commands.Bot(command_prefix=commands.when_mentioned_or(".", f"{ghost_unicode} ", ghost_unicode))

if __name__ == '__main__':
    # Scan for files in the /cogs/ directory and make a list of the file names.
    cogs = [file.stem for file in Path('cogs').glob('*.py')]
    for extension in cogs:
        try:
            bot.load_extension(f'cogs.{extension}')
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=stderr)
            print_exc()

bot.run(HACKTOBERBOT_TOKEN)

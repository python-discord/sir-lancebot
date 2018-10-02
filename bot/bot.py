from pathlib import Path
from sys import stderr
from traceback import print_exc


from bot import constants
from discord.ext import commands


bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'))

if __name__ == '__main__':
    cogs = [x.stem for x in Path('cogs').glob('*.py')]
    for extension in cogs:
        try:
            bot.load_extension(f'cogs.{extension}')
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=stderr)
            print_exc()

bot.run(constants.token)

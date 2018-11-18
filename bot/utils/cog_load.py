import logging
from traceback import format_exc
from typing import List

from discord.ext import commands

log = logging.getLogger()


def load_cogs(bot: commands.Bot, cogs: List[str]):
    """
    Unload all current cogs, then
    load in the ones passed into `cogs`
    """

    # Unload all cogs
    extensions = list(bot.extensions.keys())
    for extension in extensions:
        bot.unload_extension(extension)

    # Load in the list of cogs that was passed in here
    for extension in cogs:
        cog = extension.split(".")[-1]
        try:
            bot.load_extension(extension)
            log.info(f'Successfully loaded extension: {cog}')
        except Exception as e:
            log.error(f'Failed to load extension {cog}: {repr(e)} {format_exc()}')

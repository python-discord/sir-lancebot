import logging
import socket
from traceback import format_exc
from typing import List

from aiohttp import AsyncResolver, ClientSession, TCPConnector
from discord.ext.commands import Bot

log = logging.getLogger(__name__)

__all__ = ('SeasonalBot',)


class SeasonalBot(Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.http_session = ClientSession(
            connector=TCPConnector(
                resolver=AsyncResolver(),
                family=socket.AF_INET,
            )
        )

    def load_extensions(self, exts: List[str]):
        """
        Unload all current cogs, then load in the ones passed into `cogs`
        """

        # Unload all cogs
        extensions = list(self.extensions.keys())
        for extension in extensions:
            self.unload_extension(extension)

        # Load in the list of cogs that was passed in here
        for extension in exts:
            cog = extension.split(".")[-1]
            try:
                self.load_extension(extension)
                log.info(f'Successfully loaded extension: {cog}')
            except Exception as e:
                log.error(f'Failed to load extension {cog}: {repr(e)} {format_exc()}')

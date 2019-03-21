import logging
import socket
from traceback import format_exc
from typing import List

from aiohttp import AsyncResolver, ClientSession, TCPConnector
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot

from bot import constants

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
            if extension != "bot.seasons":  # We shouldn't unload the manager.
                self.unload_extension(extension)

        # Load in the list of cogs that was passed in here
        for extension in exts:
            cog = extension.split(".")[-1]
            try:
                self.load_extension(extension)
                log.info(f'Successfully loaded extension: {cog}')
            except Exception as e:
                log.error(f'Failed to load extension {cog}: {repr(e)} {format_exc()}')

    async def send_log(self, title: str, details: str = None, *, icon: str = None):
        """
        Send an embed message to the devlog channel
        """
        devlog = self.get_channel(constants.Channels.devlog)

        if not devlog:
            log.warning("Log failed to send. Devlog channel not found.")
            return

        if not icon:
            icon = self.user.avatar_url_as(format="png")

        embed = Embed(description=details)
        embed.set_author(name=title, icon_url=icon)

        await devlog.send(embed=embed)

    async def on_command_error(self, context, exception):
        # Don't punish the user for getting the arguments wrong
        if isinstance(exception, commands.UserInputError):
            context.command.reset_cooldown(context)
        else:
            await super().on_command_error(context, exception)

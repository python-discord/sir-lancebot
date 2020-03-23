import asyncio
import contextlib
import logging
import socket
from typing import Optional

import async_timeout
import discord
from aiohttp import AsyncResolver, ClientSession, TCPConnector
from discord import DiscordException, Embed
from discord.ext import commands

from bot.constants import Channels, Client

log = logging.getLogger(__name__)

__all__ = ('SeasonalBot', 'bot')


class SeasonalBot(commands.Bot):
    """Base bot instance."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.http_session = ClientSession(
            connector=TCPConnector(resolver=AsyncResolver(), family=socket.AF_INET)
        )

    async def send_log(self, title: str, details: str = None, *, icon: str = None) -> None:
        """Send an embed message to the devlog channel."""
        devlog = self.get_channel(Channels.devlog)

        if not devlog:
            log.warning("Log failed to send. Devlog channel not found.")
            return

        if not icon:
            icon = self.user.avatar_url_as(format="png")

        embed = Embed(description=details)
        embed.set_author(name=title, icon_url=icon)

        await devlog.send(embed=embed)

    async def on_command_error(self, context: commands.Context, exception: DiscordException) -> None:
        """Check command errors for UserInputError and reset the cooldown if thrown."""
        if isinstance(exception, commands.UserInputError):
            context.command.reset_cooldown(context)
        else:
            await super().on_command_error(context, exception)

    @property
    def member(self) -> Optional[discord.Member]:
        """Retrieves the guild member object for the bot."""
        guild = bot.get_guild(Client.guild)
        if not guild:
            return None
        return guild.me

    async def set_avatar(self, url: str) -> bool:
        """Sets the bot's avatar based on a URL."""
        # Track old avatar hash for later comparison
        old_avatar = bot.user.avatar

        image = await self._fetch_image(url)
        with contextlib.suppress(discord.HTTPException, asyncio.TimeoutError):
            async with async_timeout.timeout(5):
                await bot.user.edit(avatar=image)

        if bot.user.avatar != old_avatar:
            log.debug(f"Avatar changed to {url}")
            return True

        log.warning(f"Changing avatar failed: {url}")
        return False

    async def set_banner(self, url: str) -> bool:
        """Sets the guild's banner based on the provided `url`."""
        guild = bot.get_guild(Client.guild)
        old_banner = guild.banner

        image = await self._fetch_image(url)
        with contextlib.suppress(discord.HTTPException, asyncio.TimeoutError):
            async with async_timeout.timeout(5):
                await guild.edit(banner=image)

        new_banner = bot.get_guild(Client.guild).banner
        if new_banner != old_banner:
            log.debug(f"Banner changed to {url}")
            return True

        log.warning(f"Changing banner failed: {url}")
        return False

    async def set_icon(self, url: str) -> bool:
        """Sets the guild's icon based on a URL."""
        guild = bot.get_guild(Client.guild)
        # Track old icon hash for later comparison
        old_icon = guild.icon

        image = await self._fetch_image(url)
        with contextlib.suppress(discord.HTTPException, asyncio.TimeoutError):
            async with async_timeout.timeout(5):
                await guild.edit(icon=image)

        new_icon = bot.get_guild(Client.guild).icon
        if new_icon != old_icon:
            log.debug(f"Icon changed to {url}")
            return True

        log.warning(f"Changing icon failed: {url}")
        return False

    async def _fetch_image(self, url: str) -> bytes:
        """Retrieve an image based on a URL."""
        log.debug(f"Getting image from: {url}")
        async with self.http_session.get(url) as resp:
            return await resp.read()

    async def set_username(self, new_name: str, nick_only: bool = False) -> Optional[bool]:
        """
        Set the bot username and/or nickname to given new name.

        Returns True/False based on success, or None if nickname fallback also failed.
        """
        old_username = self.user.name

        if nick_only:
            return await self.set_nickname(new_name)

        if old_username == new_name:
            # since the username is correct, make sure nickname is removed
            return await self.set_nickname()

        log.debug(f"Changing username to {new_name}")
        with contextlib.suppress(discord.HTTPException):
            await bot.user.edit(username=new_name, nick=None)

        if not new_name == self.member.display_name:
            # name didn't change, try to changing nickname as fallback
            if await self.set_nickname(new_name):
                log.warning(f"Changing username failed, changed nickname instead.")
                return False
            log.warning(f"Changing username and nickname failed.")
            return None

        return True

    async def set_nickname(self, new_name: str = None) -> bool:
        """Set the bot nickname in the main guild."""
        old_display_name = self.member.display_name

        if old_display_name == new_name:
            return False

        log.debug(f"Changing nickname to {new_name}")
        with contextlib.suppress(discord.HTTPException):
            await self.member.edit(nick=new_name)

        return not old_display_name == self.member.display_name


bot = SeasonalBot(command_prefix=Client.prefix)

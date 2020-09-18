import asyncio
import enum
import logging
import socket
from typing import Optional, Union

import async_timeout
import discord
from aiohttp import AsyncResolver, ClientSession, TCPConnector
from discord import DiscordException, Embed, Guild, User
from discord.ext import commands

from bot.constants import Channels, Client, MODERATION_ROLES
from bot.utils.decorators import mock_in_debug

log = logging.getLogger(__name__)

__all__ = ("AssetType", "SeasonalBot", "bot")


class AssetType(enum.Enum):
    """
    Discord media assets.

    The values match exactly the kwarg keys that can be passed to `Guild.edit` or `User.edit`.
    """

    BANNER = "banner"
    AVATAR = "avatar"
    SERVER_ICON = "icon"


class SeasonalBot(commands.Bot):
    """
    Base bot instance.

    While in debug mode, the asset upload methods (avatar, banner, ...) will not
    perform the upload, and will instead only log the passed download urls and pretend
    that the upload was successful. See the `mock_in_debug` decorator for further details.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.http_session = ClientSession(
            connector=TCPConnector(resolver=AsyncResolver(), family=socket.AF_INET)
        )
        self._guild_available = asyncio.Event()

        self.loop.create_task(self.send_log("SeasonalBot", "Connected!"))

    @property
    def member(self) -> Optional[discord.Member]:
        """Retrieves the guild member object for the bot."""
        guild = self.get_guild(Client.guild)
        if not guild:
            return None
        return guild.me

    def add_cog(self, cog: commands.Cog) -> None:
        """
        Delegate to super to register `cog`.

        This only serves to make the info log, so that extensions don't have to.
        """
        super().add_cog(cog)
        log.info(f"Cog loaded: {cog.qualified_name}")

    async def on_command_error(self, context: commands.Context, exception: DiscordException) -> None:
        """Check command errors for UserInputError and reset the cooldown if thrown."""
        if isinstance(exception, commands.UserInputError):
            context.command.reset_cooldown(context)
        else:
            await super().on_command_error(context, exception)

    async def _fetch_image(self, url: str) -> bytes:
        """Retrieve and read image from `url`."""
        log.debug(f"Getting image from: {url}")
        async with self.http_session.get(url) as resp:
            return await resp.read()

    async def _apply_asset(self, target: Union[Guild, User], asset: AssetType, url: str) -> bool:
        """
        Internal method for applying media assets to the guild or the bot.

        This shouldn't be called directly. The purpose of this method is mainly generic
        error handling to reduce needless code repetition.

        Return True if upload was successful, False otherwise.
        """
        log.info(f"Attempting to set {asset.name}: {url}")

        kwargs = {asset.value: await self._fetch_image(url)}
        try:
            async with async_timeout.timeout(5):
                await target.edit(**kwargs)

        except asyncio.TimeoutError:
            log.info("Asset upload timed out")
            return False

        except discord.HTTPException as discord_error:
            log.exception("Asset upload failed", exc_info=discord_error)
            return False

        else:
            log.info("Asset successfully applied")
            return True

    @mock_in_debug(return_value=True)
    async def set_banner(self, url: str) -> bool:
        """Set the guild's banner to image at `url`."""
        guild = self.get_guild(Client.guild)
        if guild is None:
            log.info("Failed to get guild instance, aborting asset upload")
            return False

        return await self._apply_asset(guild, AssetType.BANNER, url)

    @mock_in_debug(return_value=True)
    async def set_icon(self, url: str) -> bool:
        """Sets the guild's icon to image at `url`."""
        guild = self.get_guild(Client.guild)
        if guild is None:
            log.info("Failed to get guild instance, aborting asset upload")
            return False

        return await self._apply_asset(guild, AssetType.SERVER_ICON, url)

    @mock_in_debug(return_value=True)
    async def set_avatar(self, url: str) -> bool:
        """Set the bot's avatar to image at `url`."""
        return await self._apply_asset(self.user, AssetType.AVATAR, url)

    @mock_in_debug(return_value=True)
    async def set_nickname(self, new_name: str) -> bool:
        """Set the bot nickname in the main guild to `new_name`."""
        member = self.member
        if member is None:
            log.info("Failed to get bot member instance, aborting asset upload")
            return False

        log.info(f"Attempting to set nickname to {new_name}")
        try:
            await member.edit(nick=new_name)
        except discord.HTTPException as discord_error:
            log.exception("Setting nickname failed", exc_info=discord_error)
            return False
        else:
            log.info("Nickname set successfully")
            return True

    async def send_log(self, title: str, details: str = None, *, icon: str = None) -> None:
        """Send an embed message to the devlog channel."""
        await self.wait_until_guild_available()
        devlog = self.get_channel(Channels.devlog)

        if not devlog:
            log.info(f"Fetching devlog channel as it wasn't found in the cache (ID: {Channels.devlog})")
            try:
                devlog = await self.fetch_channel(Channels.devlog)
            except discord.HTTPException as discord_exc:
                log.exception("Fetch failed", exc_info=discord_exc)
                return

        if not icon:
            icon = self.user.avatar_url_as(format="png")

        embed = Embed(description=details)
        embed.set_author(name=title, icon_url=icon)

        await devlog.send(embed=embed)

    async def on_guild_available(self, guild: discord.Guild) -> None:
        """
        Set the internal `_guild_available` event when PyDis guild becomes available.

        If the cache appears to still be empty (no members, no channels, or no roles), the event
        will not be set.
        """
        if guild.id != Client.guild:
            return

        if not guild.roles or not guild.members or not guild.channels:
            log.warning("Guild available event was dispatched but the cache appears to still be empty!")
            return

        self._guild_available.set()

    async def on_guild_unavailable(self, guild: discord.Guild) -> None:
        """Clear the internal `_guild_available` event when PyDis guild becomes unavailable."""
        if guild.id != Client.guild:
            return

        self._guild_available.clear()

    async def wait_until_guild_available(self) -> None:
        """
        Wait until the PyDis guild becomes available (and the cache is ready).

        The on_ready event is inadequate because it only waits 2 seconds for a GUILD_CREATE
        gateway event before giving up and thus not populating the cache for unavailable guilds.
        """
        await self._guild_available.wait()


_allowed_roles = [discord.Object(id_) for id_ in MODERATION_ROLES]
bot = SeasonalBot(
    command_prefix=Client.prefix,
    activity=discord.Game(name=f"Commands: {Client.prefix}help"),
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=_allowed_roles),
)

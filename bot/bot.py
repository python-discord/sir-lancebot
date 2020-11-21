import asyncio
import logging
import socket
from typing import Optional

import discord
from aiohttp import AsyncResolver, ClientSession, TCPConnector
from async_rediscache import RedisSession
from discord import DiscordException, Embed
from discord.ext import commands

from bot import constants

log = logging.getLogger(__name__)

__all__ = ("Bot", "bot")


class Bot(commands.Bot):
    """
    Base bot instance.

    While in debug mode, the asset upload methods (avatar, banner, ...) will not
    perform the upload, and will instead only log the passed download urls and pretend
    that the upload was successful. See the `mock_in_debug` decorator for further details.
    """

    name = constants.Client.name

    def __init__(self, redis_session: RedisSession, **kwargs):
        super().__init__(**kwargs)
        self.http_session = ClientSession(
            connector=TCPConnector(resolver=AsyncResolver(), family=socket.AF_INET)
        )
        self._guild_available = asyncio.Event()
        self.redis_session = redis_session

        self.loop.create_task(self.send_log(self.name, "Connected!"))

    @property
    def member(self) -> Optional[discord.Member]:
        """Retrieves the guild member object for the bot."""
        guild = self.get_guild(constants.Client.guild)
        if not guild:
            return None
        return guild.me

    async def close(self) -> None:
        """Close Redis session when bot is shutting down."""
        await super().close()

        if self.http_session:
            await self.http_session.close()

        if self.redis_session:
            await self.redis_session.close()

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

    async def send_log(self, title: str, details: str = None, *, icon: str = None) -> None:
        """Send an embed message to the devlog channel."""
        await self.wait_until_guild_available()
        devlog = self.get_channel(constants.Channels.devlog)

        if not devlog:
            log.info(f"Fetching devlog channel as it wasn't found in the cache (ID: {constants.Channels.devlog})")
            try:
                devlog = await self.fetch_channel(constants.Channels.devlog)
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
        if guild.id != constants.Client.guild:
            return

        if not guild.roles or not guild.members or not guild.channels:
            log.warning("Guild available event was dispatched but the cache appears to still be empty!")
            return

        self._guild_available.set()

    async def on_guild_unavailable(self, guild: discord.Guild) -> None:
        """Clear the internal `_guild_available` event when PyDis guild becomes unavailable."""
        if guild.id != constants.Client.guild:
            return

        self._guild_available.clear()

    async def wait_until_guild_available(self) -> None:
        """
        Wait until the PyDis guild becomes available (and the cache is ready).

        The on_ready event is inadequate because it only waits 2 seconds for a GUILD_CREATE
        gateway event before giving up and thus not populating the cache for unavailable guilds.
        """
        await self._guild_available.wait()


_allowed_roles = [discord.Object(id_) for id_ in constants.MODERATION_ROLES]

_intents = discord.Intents.default()  # Default is all intents except for privileged ones (Members, Presences, ...)
_intents.bans = False
_intents.integrations = False
_intents.invites = False
_intents.typing = False
_intents.webhooks = False

redis_session = RedisSession(
    address=(constants.RedisConfig.host, constants.RedisConfig.port),
    password=constants.RedisConfig.password,
    minsize=1,
    maxsize=20,
    use_fakeredis=constants.RedisConfig.use_fakeredis,
    global_namespace="sir-lancebot"
)
loop = asyncio.get_event_loop()
loop.run_until_complete(redis_session.connect())

bot = Bot(
    redis_session=redis_session,
    command_prefix=constants.Client.prefix,
    activity=discord.Game(name=f"Commands: {constants.Client.prefix}help"),
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=_allowed_roles),
    intents=_intents,
)

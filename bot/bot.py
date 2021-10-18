import asyncio
import logging
import socket
from contextlib import suppress
from typing import Optional

import discord
from aiohttp import AsyncResolver, ClientSession, TCPConnector
from async_rediscache import RedisCache, RedisSession
from discord import DiscordException, Embed, Forbidden, Thread
from discord.ext import commands
from discord.ext.commands import Cog, when_mentioned_or

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

    # This cache contains all the unloaded extensions
    # The cache is default to "unloaded", which contains all the unloaded exts
    # RedisCache["unloaded": str, str]
    unloads_cache = RedisCache()

    name = constants.Client.name

    def __init__(self, redis_session: RedisSession, **kwargs):
        super().__init__(**kwargs)
        self.http_session = ClientSession(
            connector=TCPConnector(resolver=AsyncResolver(), family=socket.AF_INET)
        )
        self._guild_available = asyncio.Event()
        self.redis_session = redis_session
        self.successfully_unloaded = []

        self.loop.create_task(self.check_channels())
        self.loop.create_task(self.send_log(self.name, "Connected!"))
        self.loop.create_task(self.process_ext_not_found())

    @property
    def member(self) -> Optional[discord.Member]:
        """Retrieves the guild member object for the bot."""
        guild = self.get_guild(constants.Client.guild)
        if not guild:
            return None
        return guild.me

    @Cog.listener()
    async def on_thread_join(self, thread: Thread) -> None:
        """
        Try to join newly created threads.

        Despite the event name being misleading, this is dispatched when new threads are created.
        We want our bots to automatically join threads in order to answer commands using their prefixes.
        """
        if thread.me:
            # Already in this thread, return early
            return

        with suppress(Forbidden):
            await thread.join()

    async def start(self, *args, **kwargs) -> None:
        """Async wrapper to load all the extensions."""
        from bot.utils.extensions import walk_extensions

        for ext in walk_extensions():
            await bot.load_extension(ext)

        await super().start(*args, **kwargs)

    async def close(self) -> None:
        """Close Redis session when bot is shutting down."""
        await super().close()

        if self.http_session:
            await self.http_session.close()

        if self.redis_session:
            await self.redis_session.close()

    async def load_extension(
        self,
        name: str,
        *,
        package: Optional[str] = None,
        ignore_cache: Optional[bool] = False
    ) -> None:
        """Load the extension only if it is not present in unloaded cache."""
        if ignore_cache and not await self.unloads_cache.get(name):
            self.successfully_unloaded.append(name)
            log.info(f"Skipping cog {name}, found in unloaded cache.")
        else:
            super().load_extension(name, package=package)

    def add_cog(self, cog: commands.Cog) -> None:
        """
        Delegate to super to register `cog`.

        This only serves to make the info log, so that extensions don't have to.
        """
        super().add_cog(cog)
        log.info(f"Cog loaded: {cog.qualified_name}")

    def add_command(self, command: commands.Command) -> None:
        """Add `command` as normal and then add its root aliases to the bot."""
        super().add_command(command)
        self._add_root_aliases(command)

    def remove_command(self, name: str) -> Optional[commands.Command]:
        """
        Remove a command/alias as normal and then remove its root aliases from the bot.

        Individual root aliases cannot be removed by this function.
        To remove them, either remove the entire command or manually edit `bot.all_commands`.
        """
        command = super().remove_command(name)
        if command is None:
            # Even if it's a root alias, there's no way to get the Bot instance to remove the alias.
            return

        self._remove_root_aliases(command)
        return command

    async def on_command_error(self, context: commands.Context, exception: DiscordException) -> None:
        """Check command errors for UserInputError and reset the cooldown if thrown."""
        if isinstance(exception, commands.UserInputError):
            context.command.reset_cooldown(context)
        else:
            await super().on_command_error(context, exception)

    async def check_channels(self) -> None:
        """Verifies that all channel constants refer to channels which exist."""
        await self.wait_until_guild_available()

        if constants.Client.debug:
            log.info("Skipping Channels Check.")
            return

        all_channels_ids = [channel.id for channel in self.get_all_channels()]
        for name, channel_id in vars(constants.Channels).items():
            if name.startswith("_"):
                continue
            if channel_id not in all_channels_ids:
                log.error(f"Channel '{name}' with ID {channel_id} missing")

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
            icon = self.user.display_avatar.url

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

    def _add_root_aliases(self, command: commands.Command) -> None:
        """Recursively add root aliases for `command` and any of its subcommands."""
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                self._add_root_aliases(subcommand)

        for alias in getattr(command, "root_aliases", ()):
            if alias in self.all_commands:
                raise commands.CommandRegistrationError(alias, alias_conflict=True)

            self.all_commands[alias] = command

    def _remove_root_aliases(self, command: commands.Command) -> None:
        """Recursively remove root aliases for `command` and any of its subcommands."""
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                self._remove_root_aliases(subcommand)

        for alias in getattr(command, "root_aliases", ()):
            self.all_commands.pop(alias, None)

    async def process_ext_not_found(self) -> None:
        """
        Process extensions which are in unloaded cache but not found on the bot.

        Send a message to #dev-alerts with the extensions, and remove them from the cache,
        """
        await self.wait_until_guild_available()
        cache_dict = await self.unloads_cache.to_dict()

        unsuccesfully_unloaded = {
            ext: link for ext, link in cache_dict.items() if ext not in self.successfully_unloaded
        }

        if not unsuccesfully_unloaded:
            return

        extensions_msg = "\n- ".join(f"`{ext}`: {msg}" for ext, msg in unsuccesfully_unloaded.items())

        dev_alerts_channel = self.get_channel(constants.Channels.dev_alerts)
        core_dev_role = self.get_guild(constants.Client.guild).get_role(constants.Roles.core_developers)
        msg = (
            f"\N{WARNING SIGN} {core_dev_role.mention}\n"
            "The following extensions were found in the cache but not on the bot:\n\n"
            f"- {extensions_msg}"
            "\n\nClearing them from the cache."
        )

        for ext in unsuccesfully_unloaded:
            await self.unloads_cache.delete(ext)

        await dev_alerts_channel.send(
            msg,
            allowed_mentions=discord.AllowedMentions(roles=[core_dev_role])
        )


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
    command_prefix=when_mentioned_or(constants.Client.prefix),
    activity=discord.Game(name=f"Commands: {constants.Client.prefix}help"),
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=_allowed_roles),
    intents=_intents,
)

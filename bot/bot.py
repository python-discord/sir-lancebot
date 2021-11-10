import asyncio
import datetime
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
from discord.ext.tasks import loop

from bot import constants

log = logging.getLogger(__name__)

__all__ = ("Bot", "bot")

DEFAULT_POINTS = 20
MAX_PER_GAME_PER_DAY_POINTS = 100


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
        self.loop.create_task(self.check_channels())
        self.loop.create_task(self.send_log(self.name, "Connected!"))

        # Mapping for the main games leaderboard
        # The key holds the name of the discord Cog and the value is the redis cache object
        # for that specific game leaderboard
        self.games_leaderboard: dict[str, tuple[RedisCache, ...]] = {}
        self.auto_per_day_leaderboard_clear.start()

    @loop(time=datetime.time.min)
    async def auto_per_day_leaderboard_clear(self) -> None:
        """Loop for clearing the per day leaderboard redis cache at UTC midnight."""
        for _, per_day_lb in self.games_leaderboard.values():
            await per_day_lb.clear()

    def ensure_leaderboard(self, cog: Cog) -> None:
        """Ensure that per day leaderboard and total leaderboard redis cache are available for the cog."""
        if self.games_leaderboard.get(cog.qualified_name):
            return

        # This cache contains the leaderboard for game `cog`
        # RedisCache[int: int]
        # Where the key is the discord user ID, and the values if the total
        # points registered for that user.
        _leaderboard_cache = RedisCache(namespace=f"{cog.qualified_name}-total")

        # This cache contains the per day leaderboard, same specifies
        _per_day_leaderboard = RedisCache(namespace=cog.qualified_name)

        self.games_leaderboard[cog.qualified_name] = (_leaderboard_cache, _per_day_leaderboard)

    async def increment_points(self, cog: Cog, user: discord.Member, points: int = DEFAULT_POINTS) -> None:
        """
        Increment points for a user in the leaderboard for game `cog` by `points`.

        If max points for today are hit for that particular game cog, then set today's points to the max
        points and add the difference of the(before today points and max possible points for a day to the
        overall points for the user.
        """
        _leaderboard_cache, _per_day_leaderboard = self.games_leaderboard.get(cog.qualified_name)

        current_points = await _leaderboard_cache.get(user.id) or 0
        current_points_today = await _per_day_leaderboard.get(user.id) or 0
        new_points_today = current_points_today + points

        if new_points_today > MAX_PER_GAME_PER_DAY_POINTS:
            log.info(f"Member({user.id}) has got maximum possible points for game cog {cog.qualified_name}.")
            await _per_day_leaderboard.set(user.id, MAX_PER_GAME_PER_DAY_POINTS)
            await _leaderboard_cache.set(
                user.id, current_points + (MAX_PER_GAME_PER_DAY_POINTS - current_points_today)
            )
        else:
            await _per_day_leaderboard.set(user.id, new_points_today)
            await _leaderboard_cache.set(user.id, current_points + points)
            log.info(
                f"Added {points} points to Member({user.id}) for game cog {cog.qualified_name}."
            )

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

    async def close(self) -> None:
        """Close Redis session when bot is shutting down."""
        await super().close()
        self.auto_per_day_leaderboard_clear.cancel()

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
                log.error(f'Channel "{name}" with ID {channel_id} missing')

    async def send_log(self, title: str, details: str = None, *, icon: str = None) -> None:
        """Send an embed message to the devlog channel."""
        await self.wait_until_guild_available()
        devlog = self.get_channel(constants.Channels.devlog)

        if not devlog:
            log.info(
                f"Fetching devlog channel as it wasn't found in the cache (ID: {constants.Channels.devlog})"
            )
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

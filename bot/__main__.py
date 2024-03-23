import asyncio

import aiohttp
import discord
from async_rediscache import RedisSession
from discord.ext import commands
from pydis_core import StartupError
from pydis_core.utils.logging import get_logger
from redis import RedisError

import bot
from bot import constants
from bot.bot import Bot
from bot.log import setup_sentry
from bot.utils.decorators import whitelist_check

log = get_logger(__name__)
setup_sentry()


async def _create_redis_session() -> RedisSession:
    """Create and connect to a redis session."""
    redis_session = RedisSession(
        host=constants.Redis.host,
        port=constants.Redis.port,
        password=constants.Redis.password.get_secret_value(),
        max_connections=20,
        use_fakeredis=constants.Redis.use_fakeredis,
        global_namespace="bot",
        decode_responses=True,
    )
    try:
        return await redis_session.connect()
    except RedisError as e:
        raise StartupError(e)


async def test_bot_in_ci(bot: Bot) -> None:
    """
    Attempt to import all extensions and then return.

    This is to ensure that all extensions can at least be
    imported and have a setup function within our CI.
    """
    from pydis_core.utils._extensions import walk_extensions

    from bot import exts

    for _ in walk_extensions(exts):
        # walk_extensions does all the heavy lifting within the generator.
        pass


async def main() -> None:
    """Entry async method for starting the bot."""
    allowed_roles = list({discord.Object(id_) for id_ in constants.MODERATION_ROLES})
    intents = discord.Intents.default()
    intents.bans = False
    intents.integrations = False
    intents.invites = False
    intents.message_content = True
    intents.typing = False
    intents.webhooks = False

    async with aiohttp.ClientSession() as session:
        bot.instance = Bot(
            guild_id=constants.Client.guild,
            http_session=session,
            redis_session=await _create_redis_session(),
            command_prefix=commands.when_mentioned_or(constants.Client.prefix),
            activity=discord.Game(name=f"Commands: {constants.Client.prefix}help"),
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=allowed_roles),
            intents=intents,
            allowed_roles=allowed_roles,
        )

        async with bot.instance as _bot:
            _bot.add_check(whitelist_check(
                channels=constants.WHITELISTED_CHANNELS,
                roles=constants.STAFF_ROLES,
            ))
            if constants.Client.in_ci:
                await test_bot_in_ci(_bot)
            else:
                await _bot.start(constants.Client.token.get_secret_value())


asyncio.run(main())

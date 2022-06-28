import asyncio
import logging

import aiohttp
import discord
from async_rediscache import RedisSession
from botcore import StartupError
from discord.ext import commands

import bot
from bot import constants
from bot.bot import Bot
from bot.utils.decorators import whitelist_check

log = logging.getLogger(__name__)


async def _create_redis_session() -> RedisSession:
    """Create and connect to a redis session."""
    redis_session = RedisSession(
        address=(constants.RedisConfig.host, constants.RedisConfig.port),
        password=constants.RedisConfig.password,
        minsize=1,
        maxsize=20,
        use_fakeredis=constants.RedisConfig.use_fakeredis,
        global_namespace="bot",
    )
    try:
        await redis_session.connect()
    except OSError as e:
        raise StartupError(e)
    return redis_session


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
            await _bot.start(constants.Client.token)


asyncio.run(main())

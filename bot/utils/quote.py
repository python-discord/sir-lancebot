"""Utility functions for fetching quotes from ZenQuotes API."""

from datetime import UTC, datetime, timedelta

from pydis_core.utils.logging import get_logger

from bot.bot import Bot

RANDOM_QUOTE_URL = "https://zenquotes.io/api/random"
DAILY_QUOTE_URL = "https://zenquotes.io/api/today"
DAILY_QUOTE_KEY="daily_quote"

log = get_logger(__name__)

def seconds_until_midnight_utc() -> int:
    """Calculate the number of seconds remaining until midnight UTC for Redis cache TTL."""
    now = datetime.now(UTC)
    tomorrow = now + timedelta(days=1)
    midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    time_to_midnight = (midnight - now)
    return int(time_to_midnight.total_seconds())


async def random_quote(bot: Bot) -> str:
    """Retrieve a random quote from ZenQuotes API."""
    async with bot.http_session.get(RANDOM_QUOTE_URL) as response:
        response.raise_for_status()
        data = await response.json()
        quote = f"{data[0]['q']}\n*— {data[0]['a']}*"
        return quote


async def daily_quote(bot: Bot) -> str:
    """Retrieve the daily quote from ZenQuotes API, cached until 00:00 UTC."""
    redis = bot.redis_session.client

    cached_quote = await redis.get(DAILY_QUOTE_KEY)
    if cached_quote:
        log.debug("Using cached daily quote.")
        return cached_quote

    log.debug("No cached quote found.")
    async with bot.http_session.get(DAILY_QUOTE_URL) as resp:
        resp.raise_for_status()
        data = await resp.json()
        quote = f"{data[0]['q']}\n*— {data[0]['a']}*"

    ttl = seconds_until_midnight_utc()

    await redis.set(DAILY_QUOTE_KEY, quote, ex=ttl)
    log.info(f"Cached daily quote for {ttl} seconds.")

    return quote

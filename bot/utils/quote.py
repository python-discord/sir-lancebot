"""Utility functions for fetching quotes from ZenQuotes API."""

from discord.ext.commands import Bot

RANDOM_QUOTE_URL = "https://zenquotes.io/api/random"
DAILY_QUOTE_URL = "https://zenquotes.io/api/today"


async def random_quote(bot: Bot) -> str:
    """Retrieve a random quote from ZenQuotes API."""
    async with bot.http_session.get(RANDOM_QUOTE_URL) as response:
        response.raise_for_status()
        data = await response.json()
        quote = f"{data[0]['q']}\n— {data[0]['a']}"
        return quote


async def daily_quote(bot: Bot) -> str:
    """Retrieve the daily quote from ZenQuotes API, cached until 00:00 UTC."""
    async with bot.http_session.get(DAILY_QUOTE_URL) as response:
            response.raise_for_status()
            data = await response.json()
            quote = f"{data[0]['q']}\n— {data[0]['a']}"
            return quote
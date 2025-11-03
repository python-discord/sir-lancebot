import aiohttp

async def random_quote() -> str:
    """Retrieves a random quote from zenquotes.io api."""
    url = "https://zenquotes.io/api/random"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return "Error: Data not Retrieved"
            data = await response.json()

            quote = f"{data[0]['q']}\n-{data[0]['a']}"
            return quote
        

async def daily_quote() -> str:
    """Retrieves the daily quote from zenquotes.io api."""
    url = "https://zenquotes.io/api/today"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return "Error: Data not Retrieved"
            data = await response.json()

            quote = f"{data[0]['q']}\n-{data[0]['a']}"
            return quote

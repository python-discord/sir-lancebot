import logging
from typing import Optional

from discord.ext import commands

log = logging.getLogger(__name__)

SEARCH_API = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={0}&format=json"
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/{0}"


class WikipediaCog(commands.Cog):
    """Get info from wikipedia."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.http_session = bot.http_session

    async def search_wikipedia(self, search_term: str) -> Optional[str]:
        """Search wikipedia and return the first page found."""
        async with self.http_session.get(SEARCH_API.format(search_term)) as response:
            data = await response.json()

        search_result = data["query"]["search"]
        if len(search_result) == 0:
            return None

        page = search_result[0]

        # we dont like "may refere to" pages.
        if "may refer to" in page["snippet"]:
            log.info(f"hit a 'may refer to' page, taking result 2 (index 1)")
            page = search_result[1]

        return page["title"]

    @commands.command(name="wikipedia", aliases=["wiki"])
    async def wikipedia(self, ctx: commands.Context, *, search: str) -> None:
        """Search for something on wikipedia."""
        title = await self.search_wikipedia(search)
        title = title.replace(" ", "_")  # wikipedia uses "_" as spaces
        await ctx.send(WIKIPEDIA_URL.format(title))


def setup(bot: commands.Bot) -> None:
    """Load the wikipedia cog."""
    bot.add_cog(WikipediaCog(bot))
    log.info("wikipedia cog loaded")

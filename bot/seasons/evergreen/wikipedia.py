import logging
from typing import List

from discord.ext import commands

log = logging.getLogger(__name__)


class WikipediaCog(commands.Cog):
    """Get info from wikipedia."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def search_wikipedia(self, search_term: str) -> List[str]:
        """Search wikipedia and return the pages found."""

    @commands.command(name="wikipedia", aliases=["wiki"])
    async def wikipedia(self, ctx: commands.Context, *, search: str) -> None:
        """Search for something on wikipedia."""
        await ctx.send(f"you searched for '{search}'")


def setup(bot: commands.Bot) -> None:
    """Load the wikipedia cog."""
    bot.add_cog(WikipediaCog(bot))
    log.info("wikipedia cog loaded")

import logging
from html import unescape
from typing import Optional
from urllib.parse import quote_plus

from discord import Embed
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

logger = logging.getLogger(__name__)


API_ROOT = "https://realpython.com/search/api/v1/"
ARTICLE_URL = "https://realpython.com{article_url}"
SEARCH_URL = "https://realpython.com/search?q={user_search}"


ERROR_EMBED = Embed(
    title="Error while searching Real Python",
    description="There was an error while trying to reach Real Python. Please try again shortly.",
    color=Colours.soft_red,
)


class RealPython(commands.Cog):
    """User initiated command to search for a Real Python article."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(aliases=["rp"])
    @commands.cooldown(1, 10, commands.cooldowns.BucketType.user)
    async def realpython(self, ctx: commands.Context, amount: Optional[int] = 5, *, user_search: str) -> None:
        """
        Send some articles from RealPython that match the search terms.

        By default the top 5 matches are sent, this can be overwritten to
        a number between 1 and 5 by specifying an amount before the search query.
        """
        if not 1 <= amount <= 5:
            await ctx.send("`amount` must be between 1 and 5 (inclusive).")
            return

        params = {"q": user_search, "limit": amount, "kind": "article"}
        async with self.bot.http_session.get(url=API_ROOT, params=params) as response:
            if response.status != 200:
                logger.error(
                    f"Unexpected status code {response.status} from Real Python"
                )
                await ctx.send(embed=ERROR_EMBED)
                return

            data = await response.json()

        articles = data["results"]

        if len(articles) == 0:
            no_articles = Embed(
                title=f"No articles found for '{user_search}'", color=Colours.soft_red
            )
            await ctx.send(embed=no_articles)
            return

        if len(articles) == 1:
            article_description = "Here is the result:"
        else:
            article_description = f"Here are the top {len(articles)} results:"

        article_embed = Embed(
            title="Search results - Real Python",
            url=SEARCH_URL.format(user_search=quote_plus(user_search)),
            description=article_description,
            color=Colours.orange,
        )

        for article in articles:
            article_embed.add_field(
                name=unescape(article["title"]),
                value=ARTICLE_URL.format(article_url=article["url"]),
                inline=False,
            )
        article_embed.set_footer(text="Click the links to go to the articles.")

        await ctx.send(embed=article_embed)


def setup(bot: Bot) -> None:
    """Load the Real Python Cog."""
    bot.add_cog(RealPython(bot))

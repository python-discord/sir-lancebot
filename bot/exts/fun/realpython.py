# Credit to Vthechamp22, who heavily inspired this bit of code
import logging
from html import unescape
from urllib.parse import quote_plus

from discord import Embed, HTTPException
from discord.ext import commands

from bot import bot
from bot.constants import Colours

logger = logging.getLogger(__name__)

API_ROOT = "https://realpython.com/search/api/v1/?"
ARTICLE_URL = "https://realpython.com{article_url}"
SEARCH_URL = "https://realpython.com/search?q={user_search}"

ERROR_EMBED = Embed(
    title="Error while searching Real Python",
    description="There was an error while trying to reach Real Python. Please try again shortly."
)


class RealPython(commands.Cog):
    """User initiated command to search for a Real Python article."""

    def __init__(self, bot: bot.Bot):
        self.bot = bot

    @commands.command(aliases=["rp"])
    @commands.cooldown(1, 10, commands.cooldowns.BucketType.user)
    async def realpython(self, ctx: commands.Context, *, user_search: str) -> None:
        """Sends 5 articles that match the user's search terms."""
        params = {"q": user_search, "limit": 5}
        async with self.bot.http_session.get(url=API_ROOT, params=params) as response:
            if response.status == 200:
                data = await response.json()
            else:
                logger.error(f"Status code is not 200, it is {response.status}")
                await ctx.send(embed=ERROR_EMBED)
                return

        if len(data["results"]) == 0:
            no_articles = Embed(
                title=f"No articles found for {user_search}",
                color=Colours.soft_red
            )
            await ctx.send(embed=no_articles)
            return

        articles = data["results"]
        encoded_user_search = quote_plus(user_search)
        embed = Embed(
            title="Search results - Real Python",
            url=SEARCH_URL.format(user_search=encoded_user_search),
            description=f"Here are the top {len(articles)} results:",
            color=Colours.orange
        )

        for article in articles:
            embed.add_field(
                name=unescape(article["title"]),
                value=(ARTICLE_URL.format(article_url=article["url"])),
                inline=False
            )
        embed.set_footer(text="Click the links to go to the articles.")

        try:
            await ctx.send(embed=embed)
        except HTTPException:
            bad_search = Embed(
                title="Your search was not Ok, please try something else.",
                color=Colours.soft_red
            )
            await ctx.send(embed=bad_search)


def setup(bot: bot.Bot) -> None:
    """Load the Real Python Cog."""
    bot.add_cog(RealPython(bot))

import logging
from html import unescape
from urllib.parse import quote_plus

from discord import Embed, HTTPException
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, Emojis

logger = logging.getLogger(__name__)

BASE_URL = "https://api.stackexchange.com/2.2/search/advanced"
SO_PARAMS = {
    "order": "desc",
    "sort": "activity",
    "site": "stackoverflow"
}
SEARCH_URL = "https://stackoverflow.com/search?q={query}"
ERR_EMBED = Embed(
    title="Error in fetching results from Stackoverflow",
    description=(
        "Sorry, there was en error while trying to fetch data from the Stackoverflow website. Please try again in some "
        "time. If this issue persists, please contact the staff or send a message in #dev-contrib."
    ),
    color=Colours.soft_red
)


class Stackoverflow(commands.Cog):
    """Contains command to interact with stackoverflow from discord."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(aliases=["so"])
    @commands.cooldown(1, 15, commands.cooldowns.BucketType.user)
    async def stackoverflow(self, ctx: commands.Context, *, search_query: str) -> None:
        """Sends the top 5 results of a search query from stackoverflow."""
        params = SO_PARAMS | {"q": search_query}
        async with self.bot.http_session.get(url=BASE_URL, params=params) as response:
            if response.status == 200:
                data = await response.json()
            else:
                logger.error(f"Status code is not 200, it is {response.status}")
                await ctx.send(embed=ERR_EMBED)
                return
        if not data["items"]:
            no_search_result = Embed(
                title=f"No search results found for {search_query}",
                color=Colours.soft_red
            )
            await ctx.send(embed=no_search_result)
            return

        top5 = data["items"][:5]
        encoded_search_query = quote_plus(search_query)
        embed = Embed(
            title="Search results - Stackoverflow",
            url=SEARCH_URL.format(query=encoded_search_query),
            description=f"Here are the top {len(top5)} results:",
            color=Colours.orange
        )
        for item in top5:
            embed.add_field(
                name=unescape(item["title"]),
                value=(
                    f"[{Emojis.reddit_upvote} {item['score']}    "
                    f"{Emojis.stackoverflow_views} {item['view_count']}     "
                    f"{Emojis.reddit_comments} {item['answer_count']}   "
                    f"{Emojis.stackoverflow_tag} {', '.join(item['tags'][:3])}]"
                    f"({item['link']})"
                ),
                inline=False)
        embed.set_footer(text="View the original link for more results.")
        try:
            await ctx.send(embed=embed)
        except HTTPException:
            search_query_too_long = Embed(
                title="Your search query is too long, please try shortening your search query",
                color=Colours.soft_red
            )
            await ctx.send(embed=search_query_too_long)


async def setup(bot: Bot) -> None:
    """Load the Stackoverflow Cog."""
    await bot.add_cog(Stackoverflow(bot))

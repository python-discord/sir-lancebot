import logging
from html import unescape
from urllib.parse import quote_plus

from discord import Embed
from discord.errors import HTTPException
from discord.ext import commands

from bot.constants import Colours

logger = logging.getLogger(__name__)

BASE_URL = "https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=activity&site=stackoverflow&q={query}"
SEARCH_URL = "https://stackoverflow.com/search?q={query}"


class Stackoverflow(commands.Cog):
    """A cog which returns the top 5 results of a query from stackoverflow."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["so"])
    @commands.cooldown(1, 15, commands.cooldowns.BucketType.user)
    async def stackoverflow(self, ctx: commands.Context, *, search_query: str) -> None:
        """Sends the top 5 results of a search query from stackoverflow."""
        for _ in range(3):
            async with self.bot.http_session.get(BASE_URL.format(query=quote_plus(search_query))) as response:
                if response.status == 200:
                    data = await response.json()
                    break
                else:
                    logger.error(f'Status code is not 200, it is {response.status}')
                    continue
        if response.status != 200:  # If the status is still not 200 after the 3 tries
            err_embed = Embed(
                title="Error in fetching results from Stackoverflow",
                description=("Sorry, there was en error while trying to fetch data from the Stackoverflow website. "
                             "Please try again in some time. If this issue persists, please contact the mods or send a "
                             "message in #dev-contrib."),
                color=Colours.soft_red
            )
            await ctx.send(embed=err_embed)
            return
        elif not data['items']:
            err_embed = Embed(
                title=f"No search results found for {search_query!r}",
                color=Colours.soft_red
            )
            await ctx.send(embed=err_embed)
            return

        top5 = data["items"][:5]
        embed = Embed(title=f"Search results for {search_query!r} - Stackoverflow",
                      url=SEARCH_URL.format(query=quote_plus(search_query)),
                      description=f"Here are the top {len(top5)} results:",
                      color=Colours.orange)
        for item in top5:
            embed.add_field(
                name=f"{unescape(item['title'])}",
                value=(f"[{item['score']} upvote{'s' if item['score'] != 1 else ''} ┃ "
                       f"{item['view_count']} view{'s' if item['view_count'] != 1 else ''} ┃ "
                       f"{item['answer_count']} answer{'s' if item['answer_count'] != 1 else ''} ┃ "
                       f"Tags: {', '.join(item['tags'])}]"
                       f"({item['link']})"),
                inline=False)
        embed.set_footer(text="View the original link for more results.")
        try:
            await ctx.send(embed=embed)
        except HTTPException:
            err_embed = Embed(
                title="Your search query is too long, please try shortening your search query",
                color=Colours.soft_red
            )
            await ctx.send(embed=err_embed)


def setup(bot: commands.Bot) -> None:
    """Loads Stackoverflow Cog."""
    bot.add_cog(Stackoverflow(bot))

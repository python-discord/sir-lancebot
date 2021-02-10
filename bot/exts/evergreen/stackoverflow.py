from html import unescape
from urllib.parse import quote_plus

from discord import Embed
from discord.ext.commands import Bot, Cog, Context, command, cooldown

BASE_URL = "https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=activity&site=stackoverflow&q={query}"
SEARCH_URL = "https://stackoverflow.com/search?q={query}"
SO_COLOR = 0xF98036


class Stackoverflow(Cog):
    """A cog which returns the top 5 results of a query from stackoverflow."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @command(name="stackoverflow", aliases=["so"])
    @cooldown(1, 15)
    async def stackoverflow(self, ctx: Context, *, search_query: str) -> None:
        """Sends the top 5 results from stackoverflow based on a search query."""
        async with self.bot.http_session.get(BASE_URL.format(query=quote_plus(search_query))) as response:
            data = await response.json()

        top5 = data["items"][:5]
        embed = Embed(title=f"Search results for {search_query!r} - Stackoverflow",
                      url=SEARCH_URL.format(query=quote_plus(search_query)),
                      description=f"Here are the top {len(top5)} results:",
                      color=SO_COLOR)
        for item in top5:
            embed.add_field(
                name=f"{unescape(item['title'])}",
                value=(f"[{item['score']} upvote{'s' if item['score'] != 1 else ''} ┃ "
                       f"{item['view_count']} view{'s' if item['view_count'] != 1 else ''} ┃ "
                       f"{item['answer_count']} answer{'s' if item['answer_count'] != 1 else ''} ┃ "
                       f"Tags: {', '.join(item['tags'])}]"
                       f"({item['link']})"),
                inline=False)
        embed.set_footer()
        await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Adds the cog to the bot."""
    bot.add_cog(Stackoverflow(bot))

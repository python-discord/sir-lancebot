from html import unescape
from urllib.parse import quote_plus

from discord import Colour, Embed
from discord.ext import commands

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
        async with self.bot.http_session.get(BASE_URL.format(query=quote_plus(search_query))) as response:
            data = await response.json()

        top5 = data["items"][:5]
        embed = Embed(title=f"Search results for {search_query!r} - Stackoverflow",
                      url=SEARCH_URL.format(query=quote_plus(search_query)),
                      description=f"Here are the top {len(top5)} results:",
                      color=Colour.orange)
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
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Adds the cog to the bot."""
    bot.add_cog(Stackoverflow(bot))

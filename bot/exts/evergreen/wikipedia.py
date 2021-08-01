import logging
import re
from datetime import datetime
from html import unescape
from typing import List, Optional

from discord import Color, Embed, TextChannel
from discord.ext import commands

from bot.bot import Bot
from bot.utils import LinePaginator

log = logging.getLogger(__name__)

SEARCH_API = (
    "https://en.wikipedia.org/w/api.php?action=query&list=search&prop=info&inprop=url&utf8=&"
    "format=json&origin=*&srlimit={number_of_results}&srsearch={string}"
)
WIKI_THUMBNAIL = (
    "https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg"
    "/330px-Wikipedia-logo-v2.svg.png"
)
WIKI_SNIPPET_REGEX = r"(<!--.*?-->|<[^>]*>)"
WIKI_SEARCH_RESULT = (
    "**[{name}]({url})**\n"
    "{description}\n"
)


class WikipediaSearch(commands.Cog):
    """Get info from wikipedia."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def wiki_request(self, channel: TextChannel, search: str) -> Optional[List[str]]:
        """Search wikipedia search string and return formatted first 10 pages found."""
        url = SEARCH_API.format(number_of_results=10, string=search)
        async with self.bot.http_session.get(url=url) as resp:
            if resp.status == 200:
                raw_data = await resp.json()
                number_of_results = raw_data["query"]["searchinfo"]["totalhits"]

                if number_of_results:
                    results = raw_data["query"]["search"]
                    lines = []

                    for article in results:
                        line = WIKI_SEARCH_RESULT.format(
                            name=article["title"],
                            description=unescape(
                                re.sub(
                                    WIKI_SNIPPET_REGEX, "", article["snippet"]
                                )
                            ),
                            url=f"https://en.wikipedia.org/?curid={article['pageid']}"
                        )
                        lines.append(line)

                    return lines

                else:
                    await channel.send(
                        "Sorry, we could not find a wikipedia article using that search term."
                    )
                    return
            else:
                log.info(f"Unexpected response `{resp.status}` while searching wikipedia for `{search}`")
                await channel.send(
                    "Whoops, the Wikipedia API is having some issues right now. Try again later."
                )
                return

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="wikipedia", aliases=("wiki",))
    async def wikipedia_search_command(self, ctx: commands.Context, *, search: str) -> None:
        """Sends paginated top 10 results of Wikipedia search.."""
        contents = await self.wiki_request(ctx.channel, search)

        if contents:
            embed = Embed(
                title="Wikipedia Search Results",
                colour=Color.blurple()
            )
            embed.set_thumbnail(url=WIKI_THUMBNAIL)
            embed.timestamp = datetime.utcnow()
            await LinePaginator.paginate(
                contents, ctx, embed
            )


def setup(bot: Bot) -> None:
    """Load the WikipediaSearch cog."""
    bot.add_cog(WikipediaSearch(bot))

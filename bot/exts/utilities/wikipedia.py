import logging
import re
from datetime import UTC, datetime
from html import unescape

from discord import Color, Embed, TextChannel
from discord.ext import commands

from bot.bot import Bot
from bot.utils import LinePaginator
from bot.utils.exceptions import APIError

log = logging.getLogger(__name__)

SEARCH_API = (
    "https://en.wikipedia.org/w/api.php"
)
WIKI_PARAMS = {
    "action": "query",
    "list": "search",
    "prop": "info",
    "inprop": "url",
    "utf8": "",
    "format": "json",
    "origin": "*",

}
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

    async def wiki_request(self, channel: TextChannel, search: str) -> list[str]:
        """Search wikipedia search string and return formatted first 10 pages found."""
        params = WIKI_PARAMS | {"srlimit": 10, "srsearch": search}
        async with self.bot.http_session.get(url=SEARCH_API, params=params) as resp:
            if resp.status != 200:
                log.info(f"Unexpected response `{resp.status}` while searching wikipedia for `{search}`")
                raise APIError("Wikipedia API", resp.status)

            raw_data = await resp.json()

            if not raw_data.get("query"):
                if error := raw_data.get("errors"):
                    log.error(f"There was an error while communicating with the Wikipedia API: {error}")
                raise APIError("Wikipedia API", resp.status, error)

            lines = []
            if raw_data["query"]["searchinfo"]["totalhits"]:
                for article in raw_data["query"]["search"]:
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

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="wikipedia", aliases=("wiki",))
    async def wikipedia_search_command(self, ctx: commands.Context, *, search: str) -> None:
        """Sends paginated top 10 results of Wikipedia search.."""
        contents = await self.wiki_request(ctx.channel, search)

        if contents:
            embed = Embed(
                title="Wikipedia Search Results",
                colour=Color.og_blurple()
            )
            embed.set_thumbnail(url=WIKI_THUMBNAIL)
            embed.timestamp = datetime.now(tz=UTC)
            await LinePaginator.paginate(contents, ctx, embed, restrict_to_user=ctx.author)
        else:
            await ctx.send(
                "Sorry, we could not find a wikipedia article using that search term."
            )


async def setup(bot: Bot) -> None:
    """Load the WikipediaSearch cog."""
    await bot.add_cog(WikipediaSearch(bot))

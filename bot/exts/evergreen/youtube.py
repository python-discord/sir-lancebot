import logging
from html import unescape
from typing import Dict, List

from discord import Embed
from discord.ext import commands
from discord.utils import escape_markdown

from bot.constants import Colours, Tokens

log = logging.getLogger(__name__)

KEY = Tokens.youtube
SEARCH_API = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v={id}"
YOUTUBE_SEARCH_URL = "https://www.youtube.com/results?search_query={search}"
RESULT = "`{index}` [{title}]({url}) - {author}"


class YouTubeSearch(commands.Cog):
    """Sends the top 5 results of a query from YouTube."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.http_session = bot.http_session

    async def search_youtube(self, search: str) -> List[Dict[str, str]]:
        """Queries API for top 5 results matching the search term."""
        results = []
        async with self.http_session.get(
            SEARCH_API,
            params={"part": "snippet", "q": search, "type": "video", "key": KEY},
        ) as response:
            if await response.status != 200:
                log.error("youtube response not succesful")
                return None

            data = await response.json()
            for item in data["items"]:
                results.append(
                    {
                        "title": escape_markdown(unescape(item["snippet"]["title"])),
                        "author": escape_markdown(
                            unescape(item["snippet"]["channelTitle"])
                        ),
                        "id": item["id"]["videoId"],
                    }
                )
        return results

    @commands.command(aliases=["yt"])
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def youtube(self, ctx: commands.Context, *, search: str) -> None:
        """Sends the top 5 results of a query from YouTube."""
        results = await self.search_youtube(search)

        if results:
            description = "\n".join(
                [
                    RESULT.format(
                        index=index,
                        title=result["title"],
                        url=YOUTUBE_VIDEO_URL.format(id=result["id"]),
                        author=result["author"],
                    )
                    for index, result in enumerate(results, start=1)
                ]
            )
            embed = Embed(
                colour=Colours.dark_green,
                title=f"YouTube results for `{search}`",
                url=YOUTUBE_SEARCH_URL.format(search=search),
                description=description,
            )
            await ctx.send(embed=embed)
        else:
            embed = Embed(
                colour=Colours.soft_red,
                title="Something went wrong :/",
                description="Sorry, we could not find a YouTube video.",
            )
            await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Load the YouTube cog."""
    bot.add_cog(YouTubeSearch(bot))

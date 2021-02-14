import logging
from dataclasses import dataclass
from html import unescape
from typing import List
from urllib.parse import quote_plus

from discord import Embed
from discord.ext import commands
from discord.utils import escape_markdown

from bot.constants import Colours, Emojis, Tokens

log = logging.getLogger(__name__)

KEY = Tokens.youtube
SEARCH_API = "https://www.googleapis.com/youtube/v3/search"
STATS_API = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v={id}"
YOUTUBE_SEARCH_URL = "https://www.youtube.com/results?search_query={search}"
RESULT = (
    "**{index}. [{title}]({url})**\n"
    "{post_detail_emoji} {user_emoji} {username} {view_emoji} {view_count} {like_emoji} {like_count}\n"
)


@dataclass
class VideoStatistics:
    """Represents YouTube video statistics."""

    view_count: int
    like_count: int


@dataclass
class Video:
    """Represents a video search result."""

    title: str
    username: str
    id: str
    video_statistics: VideoStatistics


class YouTubeSearch(commands.Cog):
    """Sends the top 5 results of a query from YouTube."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.http_session = bot.http_session

    async def get_statistics(self, id: str) -> VideoStatistics:
        """Queries API for statistics of one video."""
        async with self.http_session.get(
            STATS_API,
            params={"part": "statistics", "id": id, "key": KEY},
        ) as response:
            if response.status != 200:
                log.error(f"YouTube statistics response not succesful: response code {response.status}")
                return None

            statistics = (await response.json())["items"][0]["statistics"]

            return VideoStatistics(
                view_count=statistics["viewCount"], like_count=statistics["likeCount"]
            )

    async def search_youtube(self, search: str) -> List[Video]:
        """Queries API for top 5 results matching the search term with fifteen second cool down per user."""
        results = []
        async with self.http_session.get(
            SEARCH_API,
            params={"part": "snippet", "q": search, "type": "video", "key": KEY},
        ) as response:
            if response.status != 200:
                log.error(f"YouTube search response not succesful: response code {response.status}")
                return None

            video_snippet = await response.json()

            for item in video_snippet["items"]:
                video_statistics = await self.get_statistics(item["id"]["videoId"])

                if video_statistics is None:
                    log.warn(
                        "YouTube statistics response not succesful, aborting youtube search"
                    )
                    return None

                results.append(
                    Video(
                        title=escape_markdown(unescape(item["snippet"]["title"])),
                        username=escape_markdown(
                            unescape(item["snippet"]["channelTitle"])
                        ),
                        id=item["id"]["videoId"],
                        video_statistics=video_statistics,
                    )
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
                        title=result.title,
                        url=YOUTUBE_VIDEO_URL.format(id=result.id),
                        post_detail_emoji=Emojis.post_detail,
                        user_emoji=Emojis.user,
                        username=result.username,
                        view_emoji=Emojis.view,
                        view_count=result.video_statistics.view_count,
                        like_emoji=Emojis.like,
                        like_count=result.video_statistics.like_count,
                    )
                    for index, result in enumerate(results, start=1)
                ]
            )
            embed = Embed(
                colour=Colours.dark_green,
                title=f"{Emojis.youtube} YouTube results for `{search}`",
                url=YOUTUBE_SEARCH_URL.format(search=quote_plus(search)),
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

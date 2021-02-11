from typing import Dict, List, Optional

from discord import Embed
from discord.ext.commands import Bot, Cog, Context, command, cooldown
from discord.utils import escape_markdown

from bot.constants import Colours, Tokens

KEY = Tokens.youtube
SEARCH_API = (
    "https://youtube.googleapis.com/youtube/v3/search?"
    "part=snippet&type=video&maxResults=5&q={search_term}&key={key}"
)
YOUTUBE_URL = "https://www.youtube.com/watch?v={id}"
RESULT = "`{index}` [{title}]({url}) - {author}"


class YouTubeSearch(Cog):
    """Sends the top 5 results of a query from YouTube."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.http_session = bot.http_session

    async def search_youtube(self, search_term: str) -> Optional[List[Dict[str, str]]]:
        """Queries API for top 5 results matching the search term."""
        results = []
        async with self.http_session.get(
            SEARCH_API.format(search_term=search_term, key=KEY)
        ) as response:
            data = await response.json()
            for item in data["items"]:
                results.append(
                    {
                        "title": escape_markdown(item["snippet"]["title"]),
                        "author": escape_markdown(item["snippet"]["channelTitle"]),
                        "id": item["id"]["videoId"],
                    }
                )
        return results

    @command(name="youtube", aliases=["yt"])
    @cooldown(1, 15)
    async def youtube(self, ctx: Context, *, search: str) -> None:
        """Sends the top 5 results of a query from YouTube."""
        results = await self.search_youtube(search)

        if results:
            description = "\n".join(
                [
                    RESULT.format(
                        index=index + 1,
                        title=result["title"],
                        url=YOUTUBE_URL.format(id=result["id"]),
                        author=result["author"],
                    )
                    for index, result in enumerate(results)
                ]
            )
            embed = Embed(
                colour=Colours.soft_red,
                title=f"YouTube results for `{search}`",
                description=description,
            )
            await ctx.send(embed=embed)
        else:
            embed = Embed(
                colour=Colours.soft_red,
                title="No Results",
                description="Sorry, we could not find a YouTube video using that search term",
            )
            await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Wikipedia Cog load."""
    bot.add_cog(YouTubeSearch(bot))

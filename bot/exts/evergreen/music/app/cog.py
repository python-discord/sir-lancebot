"""Music cog module to show music information from Last.fm API."""
import logging
from typing import Any, Dict, List, Tuple

from aiohttp import ClientSession
from discord import Embed
from discord.ext.commands import Bot, Cog, Context, group

from bot.utils.extensions import invoke_help_command
from bot.utils.pagination import ImagePaginator
from . import api, utils


logger: logging.Logger = logging.getLogger(__name__)


class Music(Cog):
    """Music cog with commands to access music data from Last.fm."""

    footer_text: str = "This bot command uses the Last.fm API"

    def __init__(self, bot: Bot):
        self.bot = bot
        self.http_session: ClientSession = bot.http_session

    # Todo: Disallow mentions
    @group(name="music", aliases=[], invoke_without_command=True)
    async def music_command(self, ctx: Context) -> None:
        """
        Music command to search track info on Last.fm.

        Use without sub commands invokes the help command.
        """
        logger.info("Invoked .music command without sub commands: Invoking help command")
        await invoke_help_command(ctx)

    @music_command.command(name="toplist", aliases=["top", "list"])
    async def toplist(self, ctx: Context, count: int = 10) -> None:
        """Get the top tracks played on Last.fm."""
        method: api.ApiMethod = api.settings.chart_methods["gettoptracks"]

        parameters = {
            "method": str(method),
            "limit": count,
        }
        top_tracks_data: Dict[str: Any] = await api.get_api_json_data(api.settings, self.http_session, **parameters)
        top_tracks: List[str] = [
            f"{position}.  [{track['name']}]({track['url']}) ({track['artist']['name']})"
            for position, track
            in enumerate(top_tracks_data["tracks"]["track"], start=1)
        ]
        paginated_pages: List[List[str]] = await utils.async_paginate(top_tracks, 10)
        pages: List[Tuple[str, str]] = [("\n".join(page), "") for page in paginated_pages]
        result_count: int = len(top_tracks)
        embed = Embed(
            title=f":trophy: :musical_note: Top {result_count} Music Track{'' if result_count == 1 else 's'}",
        )
        embed.set_footer(text=self.footer_text)
        await ImagePaginator.paginate(pages=pages, ctx=ctx, embed=embed)

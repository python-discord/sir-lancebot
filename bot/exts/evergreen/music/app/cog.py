"""Music cog module to show music information from Last.fm API."""

import logging

from aiohttp import ClientSession
from discord import Embed
from discord.ext.commands import Cog, Context, group
from discord.ext.commands.errors import BadArgument

from bot.bot import Bot
from bot.utils.extensions import invoke_help_command
from bot.utils.pagination import ImagePaginator
from . import api, utils


logger = logging.getLogger(__name__)


class Music(Cog):
    """Music cog with commands to access music data from Last.fm."""

    footer_text = "This bot command uses the Last.fm API"

    def __init__(self, bot: Bot):
        self.bot = bot
        self.http_session: ClientSession = bot.http_session
        self.settings: api.LastFmApiSettings = api.settings

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
        method = self.settings.chart_methods["gettoptracks"]

        parameters = {
            "method": str(method),
            "limit": count,
        }
        try:
            top_tracks_data = await api.get(
                self.settings, self.http_session, **parameters,
            )
        except api.InvalidArgument as e:
            raise BadArgument(str(e))

        top_tracks = [
            f"{position}.  [{track['name']}]({track['url']}) ({track['artist']['name']})"
            for position, track
            in enumerate(top_tracks_data[method.item_plural][method.item], start=1)
        ]
        paginated_pages = await utils.async_paginate(top_tracks, 10)
        pages = [("\n".join(page), "") for page in paginated_pages]
        result_count = len(top_tracks)
        embed = Embed(
            title=f":trophy: :musical_note: Top {result_count} Music Track{'' if result_count == 1 else 's'}",
        )
        embed.set_footer(text=self.footer_text)
        await ImagePaginator.paginate(pages=pages, ctx=ctx, embed=embed)

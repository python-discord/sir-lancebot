"""Music cog module to show music information from Last.fm API."""
import logging
from dataclasses import dataclass

import pylast
from aiohttp import ClientSession
from discord.ext.commands import Bot, Cog, Context, group

from bot.constants import Tokens


logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class LastFmApiSettings:
    """Last.fm API settings."""

    key: str = Tokens.lastfm_api_key
    secret: str = Tokens.lastfm_client_secret
    token: str = ""
    base_url: str = "http://ws.audioscrobbler.com/2.0/"
    token_url: str = ""


api = LastFmApiSettings()
network: pylast.LastFMNetwork = pylast.LastFMNetwork(
    api_key=api.key,
    api_secret=api.secret,
)


class Music(Cog):
    """Music cog with commands to access music data from Last.fm."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.http_session: ClientSession = bot.http_session

    @group(name="music", aliases=[], invoke_without_command=True)
    async def music(self, ctx: Context, **kwargs) -> None:
        """Music command."""
        # Todo: Implement music command functionality
        logger.info("Hello from Music Cog!")


def setup(bot: Bot) -> None:
    """Load music cog."""
    bot.add_cog(Music(bot))

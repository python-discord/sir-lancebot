import logging

from bot.bot import Bot
from bot.constants import Tokens


logger = logging.getLogger(__name__)


def setup(bot: Bot) -> None:
    """Load Music cog."""
    if not Tokens.lastfm_api_key:
        logger.error("Failed to load the Music cog as lastfm_api_key is missing.")
        return

    from bot.exts.evergreen.music.app.cog import Music
    bot.add_cog(Music(bot))

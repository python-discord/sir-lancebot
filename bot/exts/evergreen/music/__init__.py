import logging

from discord.ext import commands

from bot.exts.evergreen.music.app.cog import Music


logger: logging.Logger = logging.getLogger(__name__)


def setup(bot: commands.Bot) -> None:
    """Load Music cog."""
    bot.add_cog(Music(bot))

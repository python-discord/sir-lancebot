import logging

from discord.ext import commands

log = logging.getLogger(__name__)


class Wikipedia(commands.Cog):
    """Get info from wikipedia."""


def setup(bot: commands.Bot) -> None:
    """Load the wikipedia cog."""
    bot.add_cog(Wikipedia())
    log.info("wikipedia cog loaded")

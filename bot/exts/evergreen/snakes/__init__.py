import logging

from discord.ext import commands

from bot.seasons.evergreen.snakes.snakes_cog import Snakes

log = logging.getLogger(__name__)


def setup(bot: commands.Bot) -> None:
    """Snakes Cog load."""
    bot.add_cog(Snakes(bot))
    log.info("Snakes cog loaded")

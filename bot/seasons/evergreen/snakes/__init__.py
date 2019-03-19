import logging

from bot.seasons.evergreen.snakes.snakes_cog import Snakes

log = logging.getLogger(__name__)


def setup(bot):
    """Snakes Cog load."""

    bot.add_cog(Snakes(bot))
    log.info("Cog loaded: Snakes")

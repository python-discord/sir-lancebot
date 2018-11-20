import logging

from bot.seasons.season import SeasonBase, SeasonManager, get_season

__all__ = ("SeasonBase", "get_season")

log = logging.getLogger(__name__)


def setup(bot):
    bot.add_cog(SeasonManager(bot))
    log.debug("SeasonManager cog loaded")

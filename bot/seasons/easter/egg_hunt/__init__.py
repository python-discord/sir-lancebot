import logging

from .cog import EggHunt

log = logging.getLogger(__name__)


def setup(bot):
    """Easter Egg Hunt Cog load."""

    bot.add_cog(EggHunt())
    log.info("EggHunt cog loaded")

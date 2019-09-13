import logging

from discord.ext import commands

from .cog import EggHunt

log = logging.getLogger(__name__)


def setup(bot: commands.Bot) -> None:
    """Easter Egg Hunt Cog load."""
    bot.add_cog(EggHunt())
    log.info("EggHunt cog loaded")

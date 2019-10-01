import logging

from discord.ext import commands

from .time_cog import Time

log = logging.getLogger(__name__)


def setup(bot: commands.Bot) -> None:
    """Time Cog load."""
    bot.add_cog(Time(bot))
    log.info("Time cog loaded")

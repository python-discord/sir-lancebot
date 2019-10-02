import logging

from discord.ext import commands

from bot.seasons.season import SeasonBase, SeasonManager, get_season

__all__ = ("SeasonBase", "get_season")

log = logging.getLogger(__name__)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(SeasonManager(bot))
    log.info("SeasonManager cog loaded")

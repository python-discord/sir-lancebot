import logging

from discord.ext import commands

log = logging.getLogger(__name__)


class SpookyEightBall(commands.Cog):
    """Find a random hacktober python issue on GitHub."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot


def setup(bot: commands.Bot) -> None:
    """Hacktober issue finder Cog Load."""
    bot.add_cog(SpookyEightBall(bot))
    log.info("hacktober-issue-finder cog loaded")

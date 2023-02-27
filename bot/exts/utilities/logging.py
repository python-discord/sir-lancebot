from discord.ext.commands import Cog
from pydis_core.utils.logging import get_logger

from bot import constants
from bot.bot import Bot

log = get_logger(__name__)


class Logging(Cog):
    """Debug logging module."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        """Announce our presence to the configured dev-log channel after checking channel constants."""
        await self.check_channels()
        await self.bot.log_to_dev_log(
            title=self.bot.name,
            details="Connected!",
        )

    async def check_channels(self) -> None:
        """Verifies that all channel constants refer to channels which exist."""
        if constants.Client.debug:
            log.info("Skipping Channels Check.")
            return

        all_channels_ids = [channel.id for channel in self.bot.get_all_channels()]
        for name, channel_id in vars(constants.Channels).items():
            if name.startswith("_"):
                continue
            if channel_id not in all_channels_ids:
                log.error(f'Channel "{name}" with ID {channel_id} missing')


async def setup(bot: Bot) -> None:
    """Load the Logging cog."""
    await bot.add_cog(Logging(bot))

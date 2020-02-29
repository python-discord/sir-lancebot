import logging

from discord.ext.commands import Cog

from bot.bot import SeasonalBot
from bot.constants import Tokens

logger = logging.getLogger(__name__)

# NASA API base URL
BASE_URL = "https://api.nasa.gov/"

# Default Parameters:
# .apod command default request parameters
APOD_PARAMS = {
    "api_key": Tokens.nasa,
    "hd": True
}


class Space(Cog):
    """Space Cog contains commands, that show images, facts or other information about space."""

    def __init__(self, bot: SeasonalBot):
        self.bot = bot
        self.http_session = bot.http_session


def setup(bot: SeasonalBot) -> None:
    """Load Space Cog."""
    # Check does bot have NASA API key in .env, when not, don't load Cog and print warning
    if not Tokens.nasa:
        logger.warning("Can't find NASA API key. Not loading Space Cog.")
        return

    bot.add_cog(Space(bot))

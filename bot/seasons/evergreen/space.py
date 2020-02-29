from discord.ext.commands import Cog

from bot.bot import SeasonalBot


class Space(Cog):
    """Space Cog contains commands, that show images, facts or other information about space."""

    def __init__(self, bot: SeasonalBot):
        self.bot = bot
        self.http_session = bot.http_session


def setup(bot: SeasonalBot) -> None:
    """Load Space Cog."""
    bot.add_cog(Space(bot))

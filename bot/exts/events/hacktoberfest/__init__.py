from bot.bot import Bot


def setup(bot: Bot) -> None:
    """Set up the Hacktoberfest extension."""
    # Import the Cog at runtime to prevent side effects like defining
    # RedisCache instances too early.
    from ._cog import Hacktoberfest

    bot.add_cog(Hacktoberfest(bot))

from bot.bot import Bot


def setup(bot: Bot) -> None:
    """Advent of Code Cog load."""
    # Import the Cog at runtime to prevent side effects like defining
    # RedisCache instances too early.
    from ._cog import AdventOfCode

    bot.add_cog(AdventOfCode(bot))

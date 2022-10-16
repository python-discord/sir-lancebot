from bot.bot import Bot


async def setup(bot: Bot) -> None:
    """Set up the Advent of Code extension."""
    # Import the Cog at runtime to prevent side effects like defining
    # RedisCache instances too early.
    from ._cog import AdventOfCode

    await bot.add_cog(AdventOfCode(bot))

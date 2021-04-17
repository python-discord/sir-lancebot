from bot.bot import Bot


def setup(bot: Bot) -> None:
    """Set up the Internal Eval extension."""
    # Import the Cog at runtime to prevent side effects like defining
    # RedisCache instances too early.
    from ._internal_eval import InternalEval

    bot.add_cog(InternalEval(bot))

from bot.bot import Bot
from bot.exts.fun.latex._latex_cog import Latex


def setup(bot: Bot) -> None:
    """Load the Latex Cog."""
    bot.add_cog(Latex(bot))

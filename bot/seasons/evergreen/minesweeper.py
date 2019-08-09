from discord.ext import commands


class Minesweeper(commands.Cog):
    """play a game of minesweeper"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


def setup(bot: commands.Bot) -> None:
    """Cog load."""
    bot.add_cog(Minesweeper(bot))

import discord
from discord.ext.commands import Cog

from bot.bot import SeasonalBot


class Player:
    """Class that contains information about player and functions that interact with player."""

    def __init__(self, user: discord.User):
        self.user = user


class TicTacToe(Cog):
    """TicTacToe cog contains tic-tac-toe game commands."""

    def __init__(self, bot: SeasonalBot):
        self.bot = bot


def setup(bot: SeasonalBot) -> None:
    """Load TicTacToe Cog."""
    bot.add_cog(TicTacToe(bot))

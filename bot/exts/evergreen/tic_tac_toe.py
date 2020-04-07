import typing as t

import discord
from discord.ext.commands import Cog, Context

from bot.bot import SeasonalBot


class Player:
    """Class that contains information about player and functions that interact with player."""

    def __init__(self, user: discord.User, ctx: Context):
        self.user = user
        self.ctx = ctx


class Game:
    """Class that contains information and functions about Tic Tac Toe game."""

    def __init__(self, channel: discord.TextChannel, players: t.List[Player], ctx: Context):
        self.channel = channel
        self.players = players
        self.ctx = ctx


class TicTacToe(Cog):
    """TicTacToe cog contains tic-tac-toe game commands."""

    def __init__(self, bot: SeasonalBot):
        self.bot = bot


def setup(bot: SeasonalBot) -> None:
    """Load TicTacToe Cog."""
    bot.add_cog(TicTacToe(bot))

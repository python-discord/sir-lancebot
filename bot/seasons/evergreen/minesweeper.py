import typing

import discord
from discord.ext import commands


class Minesweeper(commands.Cog):
    """Play a game of minesweeper."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.games: typing.Dict[discord.member, typing.Dict] = {}  # Store the currently running games

    @commands.command(name="minesweeper")
    async def minesweeper_command(self, ctx: commands.Context) -> None:
        """Start a game of minesweeper."""
        if ctx.author in self.games.keys():  # Player is already playing
            msg = await ctx.send(f"{ctx.author.mention} you already have a game running")
            await msg.delete(delay=2)
            await ctx.message.delete(delay=2)
            return

        # Add game to list

        self.games[ctx.author] = {

        }


def setup(bot: commands.Bot) -> None:
    """Cog load."""
    bot.add_cog(Minesweeper(bot))

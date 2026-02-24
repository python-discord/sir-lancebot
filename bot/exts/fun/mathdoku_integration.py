
from discord.ext import commands
from mathdoku_parser import create_grids

from bot.bot import Bot

grids = create_grids()


class Mathdoku(commands.Cog):
    """Play a game of Mathdoku."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.group(name="Mathdoku", invoke_without_command=True)
    async def Mathdoku_group(self, ctx: commands.Context) -> None:
        """Commands for Playing Mathdoku."""
        await ctx.send("The Mathdoku API is working!")


async def setup(bot: Bot) -> None:
    """Load the Mathdoku cog."""
    await bot.add_cog(Mathdoku(bot))

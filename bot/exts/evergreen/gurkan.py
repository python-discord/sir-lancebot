import discord
from discord.ext import commands

from bot.constants import Colours


class Gurkan(commands.Cog):
    """Commands related to Gurkan and the Gurkult."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="gurkancount", aliases=("gc", "gurkcount"))
    async def gurkancount(self, ctx: commands.Context) -> None:
        """Get the amount of members with 'gurkan' in their names."""
        gurkans = [1 for member in ctx.guild.members if "gurkan" in member.display_name.lower()]
        gurkan_count = sum(gurkans)

        embed = discord.Embed(
            title="Gurkancount",
            color=Colours.bright_green,
            description=f"There are a total of `{gurkan_count}` gurkans in the server!")

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Load the Bookmark cog."""
    bot.add_cog(Gurkan(bot))

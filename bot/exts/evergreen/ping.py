from discord import Embed
from discord.ext import commands

from bot.constants import Colours


class Ping(commands.Cog):
    """Ping the bot to see its latency and state."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        """Ping the bot to see its latency and state."""
        embed = Embed(
            title=":ping_pong: Pong!",
            colour=Colours.bright_green,
            description=f"Gateway Latency: {round(self.bot.latency * 1000)}ms",
        )

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Cog load."""
    bot.add_cog(Ping(bot))

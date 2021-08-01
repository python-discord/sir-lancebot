import arrow
from dateutil.relativedelta import relativedelta
from discord import Embed
from discord.ext import commands

from bot import start_time
from bot.bot import Bot
from bot.constants import Colours


class Ping(commands.Cog):
    """Get info about the bot's ping and uptime."""

    def __init__(self, bot: Bot):
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

    # Originally made in 70d2170a0a6594561d59c7d080c4280f1ebcd70b by lemon & gdude2002
    @commands.command(name="uptime")
    async def uptime(self, ctx: commands.Context) -> None:
        """Get the current uptime of the bot."""
        difference = relativedelta(start_time - arrow.utcnow())
        uptime_string = start_time.shift(
            seconds=-difference.seconds,
            minutes=-difference.minutes,
            hours=-difference.hours,
            days=-difference.days
        ).humanize()

        await ctx.send(f"I started up {uptime_string}.")


def setup(bot: Bot) -> None:
    """Load the Ping cog."""
    bot.add_cog(Ping(bot))

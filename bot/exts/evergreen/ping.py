import time
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

    @commands.command(name="ping", aliases=["Latency"])
    async def ping(self, ctx):
        """Ping the bot to see its latency and state."""
        msg = await ctx.message.reply("`Bot Latency...`")
        times = []
        embed = discord.Embed(
            title="More Information:",
            description="4 pings have been made and here are the results:",
            colour=discord.Color.random()
        )

        for counter in range(4):
            start = time.perf_counter()

            await msg.edit(content=f"Trying Ping... {counter}/3")
            end = time.perf_counter()
            speed = round((end - start) * 1000)
            times.append(speed)

            if speed < 160:
                # :green_circle: --> would also work
                embed.add_field(
                    name=f"Ping {counter}:", value=f"🟢 | {speed}ms", inline=True)

            elif speed > 170:
                # :yellow_circle: --> would also work
                embed.add_field(
                    name=f"Ping {counter}:", value=f"🟡 | {speed}ms", inline=True)

            else:
                # :red_circle: --> would also work
                embed.add_field(
                    name=f"Ping {counter}:", value=f"🔴 | {speed}ms", inline=True)

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

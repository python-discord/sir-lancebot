import logging

from discord.ext import commands


log = logging.getLogger(__name__)


class LemonStats(commands.Cog):
    """A cog for generating useful lemon-related statistics."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def lemoncount(self, ctx: commands.Context):
        """Count the number of users on the server with `'lemon'` in their nickname."""

        async with ctx.typing():
            lemoncount = sum(
                ['lemon' in server_member.display_name.lower() for server_member in self.bot.guilds[0].members]
            )

            await ctx.send(f"There are currently {lemoncount} lemons on the server.")


def setup(bot):
    """Load LemonStats Cog."""

    bot.add_cog(LemonStats(bot))
    log.info("LemonStats cog loaded")

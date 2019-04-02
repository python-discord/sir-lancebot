import logging
import json
import random

from discord.ext import commands

log = logging.getLogger(__name__)


class Traditions(commands.Cog):
    """A cog which allows users to get a random easter tradition or custom from a random country."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="easter_tradition")
    async def easter_tradition(self, ctx):
        """Responds with a random tradition or custom"""

        traditions = {}
        with open('userbalance.json', 'r') as f:
            traditions = json.load(f)

        random_country = random.choice(list(traditions))

        await ctx.send(f"{random_country}:\n{traditions[random_country]}")


def setup(bot):
    """Traditions Cog load."""

    bot.add_cog(Traditions(bot))
    log.info("Traditions cog loaded")

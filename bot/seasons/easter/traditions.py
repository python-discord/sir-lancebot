import json
import logging
import random
from pathlib import Path

from discord.ext import commands

log = logging.getLogger(__name__)

with open(Path("bot/resources/easter/traditions.json"), "r", encoding="utf8") as f:
    traditions = json.load(f)


class Traditions(commands.Cog):
    """A cog which allows users to get a random easter tradition or custom from a random country."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=('eastercustoms',))
    async def easter_tradition(self, ctx):
        """Responds with a random tradition or custom."""
        random_country = random.choice(list(traditions))

        await ctx.send(f"{random_country}:\n{traditions[random_country]}")


def setup(bot):
    """Traditions Cog load."""
    bot.add_cog(Traditions(bot))
    log.info("Traditions cog loaded")

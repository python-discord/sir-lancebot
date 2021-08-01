import json
import logging
import random
from pathlib import Path

from discord.ext import commands

from bot.bot import Bot

log = logging.getLogger(__name__)

traditions = json.loads(Path("bot/resources/easter/traditions.json").read_text("utf8"))


class Traditions(commands.Cog):
    """A cog which allows users to get a random easter tradition or custom from a random country."""

    @commands.command(aliases=("eastercustoms",))
    async def easter_tradition(self, ctx: commands.Context) -> None:
        """Responds with a random tradition or custom."""
        random_country = random.choice(list(traditions))

        await ctx.send(f"{random_country}:\n{traditions[random_country]}")


def setup(bot: Bot) -> None:
    """Load the Traditions Cog."""
    bot.add_cog(Traditions())

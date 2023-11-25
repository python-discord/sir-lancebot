import json
import random
from pathlib import Path

from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.bot import Bot

log = get_logger(__name__)

traditions = json.loads(Path("bot/resources/holidays/easter/traditions.json").read_text("utf8"))


class Traditions(commands.Cog):
    """A cog which allows users to get a random easter tradition or custom from a random country."""

    @commands.command(aliases=("eastercustoms",))
    async def easter_tradition(self, ctx: commands.Context) -> None:
        """Responds with a random tradition or custom."""
        random_country = random.choice(list(traditions))

        await ctx.send(f"{random_country}:\n{traditions[random_country]}")


async def setup(bot: Bot) -> None:
    """Load the Traditions Cog."""
    await bot.add_cog(Traditions())

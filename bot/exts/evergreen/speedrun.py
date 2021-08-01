import json
import logging
from pathlib import Path
from random import choice

from discord.ext import commands

from bot.bot import Bot

log = logging.getLogger(__name__)

LINKS = json.loads(Path("bot/resources/evergreen/speedrun_links.json").read_text("utf8"))


class Speedrun(commands.Cog):
    """Commands about the video game speedrunning community."""

    @commands.command(name="speedrun")
    async def get_speedrun(self, ctx: commands.Context) -> None:
        """Sends a link to a video of a random speedrun."""
        await ctx.send(choice(LINKS))


def setup(bot: Bot) -> None:
    """Load the Speedrun cog."""
    bot.add_cog(Speedrun())

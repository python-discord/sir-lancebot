import json
import logging
from pathlib import Path
from random import choice

from discord.ext import commands

log = logging.getLogger(__name__)


class Speedrun(commands.Cog):
    """Commands about the video game speedrunning community."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="speedrun")
    async def get_speedrun(self, ctx):
        """Sends a link to a video of a random speedrun."""
        with open(Path('bot/resources/evergreen/speedrun_links.json')) as file:
            data = json.load(file)
        # links = data['links']
        await ctx.send(choice(data))


def setup(bot):
    """Load the Speedrun cog"""
    bot.add_cog(Speedrun(bot))
    log.info("Speedrun cog loaded")

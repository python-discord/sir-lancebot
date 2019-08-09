import json
import logging
from pathlib import Path
from random import choice


from discord.ext import commands


log = logging.getLogger(__name__)


class Speedrun(commands.Cog):
    """A command that will link a random speedrun video from youtube to Discord."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="speedrun")
    async def get_speedrun(self, ctx):
        """
        Sends a link to Discord of a random speedrun from youtube.

        Utilizes speedrun_links.json to find links.
        """
        with open(Path('bot/resources/evergreen/speedrun_links.json')) as file:
            data = json.load(file)
        links = data['links']
        await ctx.send(choice(links))


def setup(bot):
    """Cog load"""
    bot.add_cog(Speedrun(bot))
    log.info("Speedrun cog loaded")

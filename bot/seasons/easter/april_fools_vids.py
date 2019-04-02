import logging
import random
from json import load
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)


class AprilFoolVideos(commands.Cog):
    """A cog for april fools that gets a random april fools video from youtube."""
    def __init__(self, bot):
        self.bot = bot
        self.yt_vids = self.load_json()
        self.youtubers = ['google']  # will add more in future

    @staticmethod
    def load_json():
        """A function to load json data."""
        p = Path('bot', 'resources', 'easter', 'april_fools_vids.json')
        with p.open() as json_file:
            all_vids = load(json_file)
        return all_vids

    @commands.command(name='fool')
    async def aprial_fools(self, ctx):
        """Gets a random april fools video from youtube."""
        random_youtuber = random.choice(self.youtubers)
        category = self.yt_vids[random_youtuber]
        random_vid = random.choice(category)
        embed = discord.Embed()
        embed.title = random_vid['title']
        embed.colour = Colours.yellow
        embed.description = f'Checkout this april fools video by {random_youtuber}'
        embed.url = random_vid['link']
        await ctx.send(f"Check out this April Fools' video by {random_youtuber}.\n\n{random_vid['link']}")


def setup(bot):
    """A function to add the cog."""
    bot.add_cog(AprilFoolVideos(bot))
    log.info('April Fools videos cog loaded!')

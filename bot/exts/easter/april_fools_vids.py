import logging
import random
from json import load
from pathlib import Path

from discord.ext import commands

log = logging.getLogger(__name__)


class AprilFoolVideos(commands.Cog):
    """A cog for April Fools' that gets a random April Fools' video from Youtube."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.yt_vids = self.load_json()
        self.youtubers = ['google']  # will add more in future

    @staticmethod
    def load_json() -> dict:
        """A function to load JSON data."""
        p = Path('bot/resources/easter/april_fools_vids.json')
        with p.open(encoding="utf-8") as json_file:
            all_vids = load(json_file)
        return all_vids

    @commands.command(name='fool')
    async def april_fools(self, ctx: commands.Context) -> None:
        """Get a random April Fools' video from Youtube."""
        random_youtuber = random.choice(self.youtubers)
        category = self.yt_vids[random_youtuber]
        random_vid = random.choice(category)
        await ctx.send(f"Check out this April Fools' video by {random_youtuber}.\n\n{random_vid['link']}")


def setup(bot: commands.Bot) -> None:
    """April Fools' Cog load."""
    bot.add_cog(AprilFoolVideos(bot))

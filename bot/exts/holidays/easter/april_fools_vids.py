import logging
import random
from json import loads
from pathlib import Path

from discord.ext import commands

from bot.bot import Bot

log = logging.getLogger(__name__)

ALL_VIDS = loads(Path("bot/resources/holidays/easter/april_fools_vids.json").read_text("utf-8"))


class AprilFoolVideos(commands.Cog):
    """A cog for April Fools' that gets a random April Fools' video from Youtube."""

    @commands.command(name="fool")
    async def april_fools(self, ctx: commands.Context) -> None:
        """Get a random April Fools' video from Youtube."""
        video = random.choice(ALL_VIDS)

        channel, url = video["channel"], video["url"]

        await ctx.send(f"Check out this April Fools' video by {channel}.\n\n{url}")


async def setup(bot: Bot) -> None:
    """Load the April Fools' Cog."""
    await bot.add_cog(AprilFoolVideos())

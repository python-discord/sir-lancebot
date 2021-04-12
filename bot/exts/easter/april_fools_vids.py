import logging
import random
from json import load

from discord.ext import commands

log = logging.getLogger(__name__)

with open("bot/resources/easter/april_fools_vids.json", encoding="utf-8") as f:
    ALL_VIDS = load(f)


class AprilFoolVideos(commands.Cog):
    """A cog for April Fools' that gets a random April Fools' video from Youtube."""

    @commands.command(name='fool')
    async def april_fools(self, ctx: commands.Context) -> None:
        """Get a random April Fools' video from Youtube."""
        video = random.choice(ALL_VIDS)

        channel, url = video["channel"], video["url"]

        await ctx.send(f"Check out this April Fools' video by {channel}.\n\n{url}")


def setup(bot: commands.Bot) -> None:
    """April Fools' Cog load."""
    bot.add_cog(AprilFoolVideos(bot))

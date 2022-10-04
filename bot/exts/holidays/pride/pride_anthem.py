import json
import logging
import random
from pathlib import Path
from typing import Optional

from discord.ext import commands

from bot.bot import Bot

log = logging.getLogger(__name__)

VIDEOS = json.loads(Path("bot/resources/holidays/pride/anthems.json").read_text("utf8"))


class PrideAnthem(commands.Cog):
    """Embed a random youtube video for a gay anthem!"""

    def get_video(self, genre: Optional[str] = None) -> dict:
        """
        Picks a random anthem from the list.

        If `genre` is supplied, it will pick from videos attributed with that genre.
        If none can be found, it will log this as well as provide that information to the user.
        """
        if not genre:
            return random.choice(VIDEOS)
        else:
            songs = [song for song in VIDEOS if genre.casefold() in song["genre"]]
            try:
                return random.choice(songs)
            except IndexError:
                log.info("No videos for that genre.")

    @commands.command(name="prideanthem", aliases=("anthem", "pridesong"))
    async def prideanthem(self, ctx: commands.Context, genre: str = None) -> None:
        """
        Sends a message with a video of a random pride anthem.

        If `genre` is supplied, it will select from that genre only.
        """
        anthem = self.get_video(genre)
        if anthem:
            await ctx.send(anthem["url"])
        else:
            await ctx.send("I couldn't find a video, sorry!")


async def setup(bot: Bot) -> None:
    """Load the Pride Anthem Cog."""
    await bot.add_cog(PrideAnthem())

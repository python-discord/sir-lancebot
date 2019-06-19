import json
import logging
import random
from pathlib import Path

from discord.ext import commands

log = logging.getLogger(__name__)


class PrideAnthem(commands.Cog):
    """Embed a random youtube video for a gay anthem!"""

    def __init__(self, bot):
        self.bot = bot
        self.anthems = self.load_vids()

    def get_video(self, genre: str = None) -> dict:
        """
        Picks a random anthem from the list.

        If `genre` is supplied, it will pick from videos attributed with that genre.
        If none can be found, it will log this as well as provide that information to the user.
        """
        if not genre:
            return random.choice(self.anthems)
        else:
            songs = [song for song in self.anthems if genre.casefold() in song['genre']]
            try:
                return random.choice(songs)
            except IndexError:
                log.info('No videos for that genre.')

    @staticmethod
    def load_vids() -> list:
        """Loads a list of videos from the resources folder as dictionaries."""
        with open(Path('bot/resources/pride/anthems.json').absolute(), 'r') as f:
            anthems = json.load(f)
        return anthems

    @commands.group(aliases=["prideanthem", "anthem", "pridesong"], invoke_without_command=True)
    async def send_anthem(self, ctx, genre: str = None):
        """Generates and sends message with youtube link."""
        anthem = self.get_video(genre)
        if anthem:
            await ctx.send(anthem['url'])
        else:
            await ctx.send("I couldn't find a video, sorry!")


def setup(bot):
    """Cog loader for pride anthem."""
    bot.add_cog(PrideAnthem(bot))
    log.info('Pride anthems cog loaded!')

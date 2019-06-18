import logging
from json import load
from pathlib import Path
from random import choice

from discord.ext import commands

log = logging.getLogger(__name__)


class PrideAnthem(commands.Cog):
    """Embed a random youtube video for a gay anthem!"""

    def __init__(self, bot):
        self.bot = bot
        self.anthems = self.load_vids()

    def get_video(self, genre: str = None) -> dict:
        if not genre:
            return choice(self.anthems)
        else:
            songs = [song for song in self.anthems if genre.casefold() in song['genre']]
            try:
                return choice(songs)
            except IndexError:
                log.info('No videos for that genre.')

    @staticmethod
    def load_vids() -> list:
        with open(Path('bot', 'resources', 'pride', 'anthems.json').absolute(), 'r') as f:
            anthems = load(f)
        return anthems

    @commands.command(name='prideanthem')
    async def send_anthem(self, ctx, genre: str = None):
        anthem = self.get_video(genre)
        # embed = Embed(title='Pride Anthem',
        #               description="Here is a pride anthem to check out!")
        if anthem:
            await ctx.send(anthem['url'])
        else:
            await ctx.send("I couldn't find a video, sorry!")


def setup(bot):
    """Cog loader for pride anthem"""
    bot.add_cog(PrideAnthem(bot))
    log.info('Pride anthems cog loaded!')

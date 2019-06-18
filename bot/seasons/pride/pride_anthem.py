import logging
from pathlib import Path
from json import load
from random import choice

from discord.ext import commands


log = logging.getLogger(__name__)


OPTIONS = {

}


class PrideAnthem(commands.Cog):
    """Embed a random youtube video for a gay anthem!"""

    def __init__(self, bot):
        self.bot = bot
        self.anthems = self.load_vids()

    def get_video(self, genre=None):
        if not genre:
            return choice(self.anthems)
        else:
            songs = [song for song in self.anthems if genre in song.genre]
            return choice(songs)

    @staticmethod
    def load_vids():
        with open(Path('bot', 'resources', 'pride', 'anthems.json').absolute(), 'r') as f:
            anthems = load(f)
        return anthems

    @commands.command(name='prideanthem')
    async def send_anthem(self, ctx, genre=None):
        video = self.get_video(genre)
        await ctx.send(f'Here\'s a pride anthem for you! {video.url}')


def setup(bot):
    """Cog loader for pride anthem"""
    bot.add_cog(PrideAnthem(bot))
    log.info('Pride anthems cog loaded!')

import logging
import random
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Hacktoberfest

log = logging.getLogger(__name__)


class SpookySound:
    """
    A cog that plays a spooky sound in a voice channel on command.
    """

    def __init__(self, bot):
        self.bot = bot
        self.sound_files = list(Path("bot", "resources", "halloween", "spookysounds").glob("*.mp3"))
        self.channel = None

    @commands.cooldown(rate=1, per=1)
    @commands.command(brief="Play a spooky sound, restricted to once per 2 mins")
    async def spookysound(self, ctx):
        """
        Connect to the Hacktoberbot voice channel, play a random spooky sound, then disconnect. Cannot be used more than
        once in 2 minutes.
        """
        if not self.channel:
            await self.bot.wait_until_ready()
            self.channel = self.bot.get_channel(Hacktoberfest.voice_id)

        await ctx.send("Initiating spooky sound...")
        file_path = random.choice(self.sound_files)
        src = discord.FFmpegPCMAudio(str(file_path.resolve()))
        voice = await self.channel.connect()
        voice.play(src, after=lambda e: self.bot.loop.create_task(self.disconnect(voice)))

    @staticmethod
    async def disconnect(voice):
        """
        Helper method to disconnect a given voice client.
        """
        await voice.disconnect()


def setup(bot):
    bot.add_cog(SpookySound(bot))
    log.debug("SpookySound cog loaded")

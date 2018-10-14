import random
from pathlib import Path

import discord
from discord.ext import commands

HACKTOBERBOT_VOICE_CHANNEL_ID = 101010  # Replace with actual channel ID


class SpookySound:

    def __init__(self, bot):
        self.bot = bot
        self.sound_files = list(Path("./bot/resources/spookysounds").glob("*.mp3"))
        self.channel = None

    async def on_ready(self):
        self.channel = self.bot.get_channel(HACKTOBERBOT_VOICE_CHANNEL_ID)

    @commands.cooldown(rate=1, per=120)
    @commands.command(brief="Play a spooky sound, restricted to once per 2 mins")
    async def spookysound(self, ctx):
        """
        Connect to the Hacktoberbot voice channel, play a random spooky sound, then disconnect. Cannot be used more than
        once in 2 minutes.
        """
        await ctx.send("Initiating spooky sound...")
        voice = await self.channel.connect()
        file_path = random.choice(self.sound_files)
        src = discord.FFmpegPCMAudio(str(file_path.resolve()))

        async def disconnect():
            await voice.disconnect()

        voice.play(src, after=lambda e: self.bot.loop.create_task(disconnect()))


def setup(bot):
    bot.add_cog(SpookySound(bot))

import logging
import os
from io import BytesIO

import aiohttp
import discord
from PIL import Image
from discord.ext import commands

from bot.utils.halloween import spookifications

log = logging.getLogger(__name__)


class SpookyAvatar(commands.Cog):
    """A cog that spookifies an avatar."""

    def __init__(self, bot):
        self.bot = bot

    async def get(self, url):
        """Returns the contents of the supplied url."""

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.read()

    @commands.command(name='savatar', aliases=('spookyavatar', 'spookify'),
                      brief='Spookify an user\'s avatar.')
    async def spooky_avatar(self, ctx, user: discord.Member = None):
        """A command to print the user's spookified avatar."""

        if user is None:
            user = ctx.message.author

        async with ctx.typing():
            embed = discord.Embed(colour=0xFF0000)
            embed.title = "Is this you or am I just really paranoid?"
            embed.set_author(name=str(user.name), icon_url=user.avatar_url)

            image_bytes = await ctx.author.avatar_url.read()
            im = Image.open(BytesIO(image_bytes))
            modified_im = spookifications.get_random_effect(im)
            modified_im.save(str(ctx.message.id)+'.png')
            f = discord.File(str(ctx.message.id)+'.png')
            embed.set_image(url='attachment://'+str(ctx.message.id)+'.png')

        await ctx.send(file=f, embed=embed)
        os.remove(str(ctx.message.id)+'.png')


def setup(bot):
    """Spooky avatar Cog load."""

    bot.add_cog(SpookyAvatar(bot))
    log.info("SpookyAvatar cog loaded")

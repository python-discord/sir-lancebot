import aiohttp
from io import BytesIO

from discord.ext import commands
import discord
from PIL import Image

from bot.resources import spookifications


class SpookyAvatar:

    """
    A cog that spookifies an avatar.
    """

    def __init__(self, bot):
        self.bot = bot

    async def get(self, url):
        """
        Returns the contents of the supplied url.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.read()

    @commands.command(name='savatar', aliases=['spookyavatar', 'spookify'],
                      brief='Spookify an user\'s avatar.')
    async def spookyavatar(self, ctx, user: discord.Member=None):
        """
        A command to print the user's spookified avatar.
        """
        if user is None:
            user = ctx.message.author

        embed = discord.Embed(colour=0xFF0000)
        embed.title = "Is this you or am I just really paranoid?"
        embed.set_author(name=str(user.name), icon_url=user.avatar_url)
        resp = await self.get(user.avatar_url)
        im = Image.open(BytesIO(resp))
        modified_im = spookifications.get_random_effect(im)
        modified_im.save(str(ctx.message.id)+'.png')
        f = discord.File(str(ctx.message.id)+'.png')
        embed.set_image(url='attachment://'+str(ctx.message.id)+'.png')
        await ctx.send(file=f, embed=embed)


def setup(bot):
    bot.add_cog(SpookyAvatar(bot))

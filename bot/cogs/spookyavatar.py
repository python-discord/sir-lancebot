from discord.ext import commands
import discord
import aiohttp
from PIL import ImageOps
from PIL import Image
from io import BytesIO


class SpookyAvatar:

    """
    A cog that spookifies an avatar.
    """

    def __init__(self, bot):
        self.bot = bot

    async def get(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.read()

    @commands.command(name='savatar', aliases=['spookyavatar', 'spookify'], brief='Spookify an user\'s avatar.')
    async def repository(self, ctx, user: discord.Member=None):
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
        im = im.convert('RGB')
        inv = ImageOps.invert(im)
        inv.save(str(ctx.message.id)+'.png')
        f = discord.File(str(ctx.message.id)+'.png')
        embed.set_image(url='attachment://'+str(ctx.message.id)+'.png')
        await ctx.send(file=f, embed=embed)


def setup(bot):
    bot.add_cog(SpookyAvatar(bot))

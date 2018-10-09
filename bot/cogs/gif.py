from os import environ

import aiohttp
from discord.ext import commands


class Gif:

    """
    A cog to fetch a random spooky gif from the web!
    """

    def __init__(self, bot):
        self.bot = bot
        self.GIPHY_TOKEN = environ.get('GIPHY_TOKEN')

    @commands.command()
    async def gif(self, ctx):
        async with aiohttp.ClientSession() as session:
            params = {'api_key': self.GIPHY_TOKEN, 'tag': 'halloween', 'rating': 'g'}
            # Make a GET request to the Giphy API to get a random halloween gif.
            async with session.get('http://api.giphy.com/v1/gifs/random', params=params) as resp:
                data = await resp.json()
            url = data['data']['url']
            await ctx.send(url)


def setup(bot):
    bot.add_cog(Gif(bot))

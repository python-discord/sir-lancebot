import logging
import random
from urllib import parse
from os import environ

import aiohttp
import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class MovieGenerator:
    """
    a cog that gives random romance movie suggestion to a user

    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def romancemovie(self, ctx):
        """

        randomly selects romance movie and displays info about it
        """

        TMDB_API_KEY = environ.get("TMDB_API_KEY")
        # selecting a random int to parse it to the page parameter
        random_page = random.randint(0, 20)
        # TMDB api params
        params = {'api_key': TMDB_API_KEY,
                  'language': 'en-US',
                  'sort_by': 'popularity.desc',
                  'include_adult': 'false',
                  'include_video': 'false',
                  'page': random_page,
                  'with_genres': '10749'
                  }
        # the api request url
        request_url = "https://api.themoviedb.org/3/discover/movie?" + parse.urlencode(params)
        async with aiohttp.ClientSession() as session:
            async with session.get(request_url) as resp:
                print(await resp.json())
                # loading the json file returned from the api
                data = await resp.json()
                # selecting random result from results object in the json file
                selected_movie = random.choice(data['results'])

        embed = discord.Embed(
            title=":sparkling_heart: " + selected_movie['title'] + ":sparkling_heart: ",
            description=selected_movie['overview'],
        )
        embed.set_image(url='http://image.tmdb.org/t/p/w200/' + selected_movie['poster_path'])
        embed.add_field(name='release date :clock1:', value=selected_movie['release_date'])
        embed.add_field(name='rating :star2: ', value=selected_movie['vote_average'])
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(MovieGenerator(bot))
    log.debug("Random movie generator cog loaded!")

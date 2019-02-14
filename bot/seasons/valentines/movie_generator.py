import discord
import logging
from discord.ext import commands
import random
import json
from urllib import parse, request
log = logging.getLogger(__name__)


class MovieGenerator:
    """
    a cog that gives random romance movie suggestion to a user

    """

    def __init__(self,bot):
        self.bot = bot

    @commands.command()
    async def movie(self, ctx):
        # selecting a random int to parse it to the page parameter
        random_page = random.randint(0, 20)
        # TMDB api params
        params = {'api_key': 'Api key here.',
                  'language': 'en-US',
                  'sort_by': 'popularity.desc',
                  'include_adult': 'false',
                  'include_video': 'false',
                  'page': random_page,
                  'with_genres': '10749'
                  }
        # the api request url
        request_url = "https://api.themoviedb.org/3/discover/movie?" + parse.urlencode(params)
        with request.urlopen(request_url) as url:
            # loading the json file returned from the api
            data = json.loads(url.read().decode())
            # selecting random result from results object in the json file
            selected_movie = random.choice(data['results'])

        embed = discord.Embed(
            title=selected_movie['title'],
            description=selected_movie['overview'],
        )
        embed.set_image(url='http://image.tmdb.org/t/p/w200/' + selected_movie['poster_path'])
        embed.add_field(name='release_date', value=selected_movie['release_date'])
        embed.add_field(name='rating', value=selected_movie['vote_average'])
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(MovieGenerator(bot))
    log.debug("Random movie generator cog loaded!")








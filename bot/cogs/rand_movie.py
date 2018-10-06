import requests
import random
from pprint import pprint
from discord.ext import commands

class Movies:

    """
    TODO.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='movie', aliases=['rand_movie', 'movie'], brief='Pick a scary movie')
    async def repository(self, ctx):
        await ctx.send('https://github.com/discord-python/hacktoberbot')

    @staticmethod
    def select_movie(api_key):
        params = {
            'apikey': api_key,
            'type': 'movie',
            's': 'halloween'
        }

        response = requests.get('http://www.omdbapi.com/', params)

        movies = []

        for movie in response.json().get('Search'):
            movie_id = movie.get('imdbID')
            movies.append(movie_id)

        selection = random.choice(movies)

        params = {
            'apikey': api_key,
            'i': selection
        }

        response = requests.get('http://www.omdbapi.com/', params)

        return response.json()


    # @commands.group(name='git', invoke_without_command=True)
    # async def github(self, ctx):
    #     """
    #     A command group with the name git. You can now create sub-commands such as git commit.
    #     """
    #
    #     await ctx.send('Resources to learn **Git**: https://try.github.io/.')
    #
    # @github.command()
    # async def commit(self, ctx):
    #     """
    #     A command that belongs to the git command group. Invoked using git commit.
    #     """
    #
    #     await ctx.send('`git commit -m "First commit"` commits tracked changes.')


# Required in order to load the cog, use the class name in the add_cog function.
def setup(bot):
    bot.add_cog(Template(bot))

import requests
import random
from discord.ext import commands
from os import environ

OMDB_API_KEY = environ.get('OMDB_API_KEY')


class Movie:
    """
    Prints the details of a random scary movie to discord chat
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='movie', aliases=['scary_movie'], brief='Pick me a scary movie')
    async def random_movie(self, ctx):
        selection = await self.select_movie()
        movie_details = await self.format_metadata(selection)

        await ctx.send(movie_details)

    @staticmethod
    async def select_movie():
        """
        Selects a random movie and returns a json of movie details from omdb
        """

        # TODO: Come up w/ a scary movie list to select from. Currently returns random Halloween movie
        omdb_params = {
            'apikey': OMDB_API_KEY,
            'type': 'movie',
            's': 'halloween'
        }
        response = requests.get('http://www.omdbapi.com/', omdb_params)

        movies = []
        for movie in response.json().get('Search'):
            movie_id = movie.get('imdbID')
            movies.append(movie_id)

        selection = random.choice(movies)

        omdb_params = {
            'apikey': OMDB_API_KEY,
            'i': selection
        }
        response = requests.get('http://www.omdbapi.com/', omdb_params)

        return response.json()

    @staticmethod
    async def format_metadata(movie):
        """
        Formats raw omdb data to be displayed in discord chat
        """
        display_text = f"You should watch {movie.get('Title')} ({movie.get('Year')})\n" \
                       f"https://www.imdb.com/title/{movie.get('imdbID')}"

        return display_text


def setup(bot):
    bot.add_cog(Movie(bot))

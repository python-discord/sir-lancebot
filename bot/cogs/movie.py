import requests
import random
from os import environ
from discord.ext import commands
from discord import Embed

TMDB_API_KEY = environ.get('TMDB_API_KEY')
TMDB_TOKEN = environ.get('TMDB_TOKEN')


class Movie:
    """
    Selects a random scary movie and embeds info into discord chat
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='movie', alias=['tmdb'], brief='Pick a scary movie')
    async def random_movie(self, ctx):
        selection = await self.select_movie()
        movie_details = await self.format_metadata(selection)

        await ctx.send(embed=movie_details)

    @staticmethod
    async def select_movie():
        """
        Selects a random movie and returns a json of movie details from TMDb
        """

        url = 'https://api.themoviedb.org/4/discover/movie'
        params = {
            'with_genres': '27',
            'vote_count.gte': '5'
        }
        headers = {
            'Authorization': 'Bearer ' + TMDB_TOKEN,
            'Content-Type': 'application/json;charset=utf-8'
        }

        # Get total page count of horror movies
        response = requests.get(url=url, params=params, headers=headers)
        total_pages = response.json().get('total_pages')

        # Get movie details from one random result on a random page
        params['page'] = random.randint(1, total_pages)
        response = requests.get(url=url, params=params, headers=headers)
        selection_id = random.choice(response.json().get('results')).get('id')

        # Get full details and credits
        selection = requests.get(url='https://api.themoviedb.org/3/movie/' + str(selection_id),
                                 params={'api_key': TMDB_API_KEY, 'append_to_response': 'credits'})

        return selection.json()

    @staticmethod
    async def format_metadata(movie):
        """
        Formats raw TMDb data to be embedded in discord chat
        """

        tmdb_url = 'https://www.themoviedb.org/movie/' + str(movie.get('id'))
        poster = 'https://image.tmdb.org/t/p/original' + movie.get('poster_path')

        cast = []
        for actor in movie.get('credits').get('cast')[:3]:
            cast.append(actor.get('name'))

        director = movie.get('credits').get('crew')[0].get('name')

        rating_count = movie.get('vote_average') / 2
        rating = ''

        for i in range(int(rating_count)):
            rating += ':skull:'

        if (rating_count % 1) >= .5:
            rating += ':bat:'

        embed = Embed(
            colour=0x01d277,
            title='**' + movie.get('title') + '**',
            url=tmdb_url,
            description=movie.get('overview')
        )
        embed.set_image(url=poster)
        embed.add_field(name='Starring', value=', '.join(cast))
        embed.add_field(name='Directed by', value=director)
        embed.add_field(name='Year', value=movie.get('release_date')[:4])
        embed.add_field(name='Runtime', value=str(movie.get('runtime')) + ' min')
        embed.add_field(name='Spooky Rating', value=rating)
        embed.set_footer(text='powered by themoviedb.org')

        return embed


def setup(bot):
    bot.add_cog(Movie(bot))

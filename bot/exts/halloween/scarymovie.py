import logging
import random
from os import environ

import aiohttp
from discord import Embed
from discord.ext import commands

log = logging.getLogger(__name__)


TMDB_API_KEY = environ.get('TMDB_API_KEY')
TMDB_TOKEN = environ.get('TMDB_TOKEN')


class ScaryMovie(commands.Cog):
    """Selects a random scary movie and embeds info into Discord chat."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='scarymovie', alias=['smovie'])
    async def random_movie(self, ctx: commands.Context) -> None:
        """Randomly select a scary movie and display information about it."""
        async with ctx.typing():
            selection = await self.select_movie()
            movie_details = await self.format_metadata(selection)

        await ctx.send(embed=movie_details)

    @staticmethod
    async def select_movie() -> dict:
        """Selects a random movie and returns a JSON of movie details from TMDb."""
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
        async with aiohttp.ClientSession() as session:
            response = await session.get(url=url, params=params, headers=headers)
            total_pages = await response.json()
            total_pages = total_pages.get('total_pages')

            # Get movie details from one random result on a random page
            params['page'] = random.randint(1, total_pages)
            response = await session.get(url=url, params=params, headers=headers)
            response = await response.json()
            selection_id = random.choice(response.get('results')).get('id')

            # Get full details and credits
            selection = await session.get(
                url='https://api.themoviedb.org/3/movie/' + str(selection_id),
                params={'api_key': TMDB_API_KEY, 'append_to_response': 'credits'}
            )

            return await selection.json()

    @staticmethod
    async def format_metadata(movie: dict) -> Embed:
        """Formats raw TMDb data to be embedded in Discord chat."""
        # Build the relevant URLs.
        movie_id = movie.get("id")
        poster_path = movie.get("poster_path")
        tmdb_url = f'https://www.themoviedb.org/movie/{movie_id}' if movie_id else None
        poster = f'https://image.tmdb.org/t/p/original{poster_path}' if poster_path else None

        # Get cast names
        cast = []
        for actor in movie.get('credits', {}).get('cast', [])[:3]:
            cast.append(actor.get('name'))

        # Get director name
        director = movie.get('credits', {}).get('crew', [])
        if director:
            director = director[0].get('name')

        # Determine the spookiness rating
        rating = ''
        rating_count = movie.get('vote_average', 0)

        if rating_count:
            rating_count /= 2

        for _ in range(int(rating_count)):
            rating += ':skull:'
        if (rating_count % 1) >= .5:
            rating += ':bat:'

        # Try to get year of release and runtime
        year = movie.get('release_date', [])[:4]
        runtime = movie.get('runtime')
        runtime = f"{runtime} minutes" if runtime else None

        # Not all these attributes will always be present
        movie_attributes = {
            "Directed by": director,
            "Starring": ', '.join(cast),
            "Running time": runtime,
            "Release year": year,
            "Spookiness rating": rating,
        }

        embed = Embed(
            colour=0x01d277,
            title='**' + movie.get('title') + '**',
            url=tmdb_url,
            description=movie.get('overview')
        )

        if poster:
            embed.set_image(url=poster)

        # Add the attributes that we actually have data for, but not the others.
        for name, value in movie_attributes.items():
            if value:
                embed.add_field(name=name, value=value)

        embed.set_footer(text="This product uses the TMDb API but is not endorsed or certified by TMDb.")
        embed.set_thumbnail(url="https://i.imgur.com/LtFtC8H.png")

        return embed


def setup(bot: commands.Bot) -> None:
    """Scary movie Cog load."""
    bot.add_cog(ScaryMovie(bot))

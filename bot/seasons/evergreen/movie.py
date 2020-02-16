import logging
import random
from enum import Enum
from os import environ
from typing import Any, Dict, List, Tuple
from urllib.parse import urlencode

from aiohttp import ClientSession
from discord import Embed
from discord.ext.commands import Bot, Cog, Context, command

from bot.pagination import ImagePaginator

# Get TMDB API key from .env
TMDB_API_KEY = environ.get('TMDB_API_KEY')

# Define base URL of TMDB
BASE_URL = "https://api.themoviedb.org/3/"

logger = logging.getLogger(__name__)

# Define movie params, that will be used for every movie request
MOVIE_PARAMS = {
    "api_key": TMDB_API_KEY,
    "language": "en-US"
}


class MovieGenres(Enum):
    """Movies Genre names and IDs."""

    Action = "28"
    Adventure = "12"
    Animation = "16"
    Comedy = "35"
    Crime = "80"
    Documentary = "99"
    Drama = "18"
    Family = "10751"
    Fantasy = "14"
    History = "36"
    Horror = "27"
    Music = "10402"
    Mystery = "9648"
    Romance = "10749"
    Science = "878"
    Thriller = "53"
    Western = "37"


class Movie(Cog):
    """Movie Cog contains movies command that grab random movies from TMDB."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.http_session: ClientSession = bot.http_session

    @command(name='movies', aliases=['movie'])
    async def movies(self, ctx: Context, genre: str = "", amount: int = 5) -> None:
        """
        Get random movies by specifing genre.

        Also support amount parameter,
        that define how much movies will be shown. Default 5

        Available genres:
        - Action
        - Adventure
        - Animation
        - Comedy
        - Crime
        - Documentary
        - Drama
        - Family
        - Fantasy
        - History
        - Horror
        - Music
        - Mystery
        - Romance
        - Science
        - Thriller
        - Western
        """
        # Check is there more than 20 movies specified, due TMDB return 20 movies
        # per page, so this is max. Also you can't get less movies than 1, just logic
        if amount > 20:
            await ctx.send("You can't get more than 20 movies at once. (TMDB limits)")
            return
        elif amount < 1:
            await ctx.send("You can't get less than 1 movies. Just logic.")
            return

        # Capitalize genre for getting data from Enum, get random page
        genre = genre.capitalize()
        page = random.randint(1, 200)

        # Get movies list from TMDB, check is results key in result. When not, raise error. When genre not exist,
        # show help.
        try:
            movies = await self.get_movies_list(self.http_session, MovieGenres[genre].value, page)
        except KeyError:
            await ctx.send_help('movies')
            return
        if 'results' not in movies.keys():
            err_text = f'There was problem while fetching movies list. Problematic response:\n```{movies}```'
            err = Embed(title=':no_entry: Error :no_entry:', description=err_text)

            await ctx.send(embed=err)
            logger.warning(err_text)

            return

        # Get all pages and embed
        pages = await self.get_pages(self.http_session, movies, amount)
        embed = await self.get_embed(genre)

        await ImagePaginator.paginate(pages, ctx, embed)

    async def get_movies_list(self, client: ClientSession, genre_id: str, page: int) -> Dict[str, Any]:
        """Return JSON of TMDB discover request."""
        # Define params of request
        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US",
            "sort_by": "popularity.desc",
            "include_adult": "false",
            "include_video": "false",
            "page": page,
            "with_genres": genre_id
        }

        url = BASE_URL + "discover/movie?" + urlencode(params)

        # Make discover request to TMDB, return result
        async with client.get(url) as resp:
            return await resp.json()

    async def get_pages(self, client: ClientSession, movies: Dict[str, Any], amount: int) -> List[Tuple[str, str]]:
        """Fetch all movie pages from movies dictionary. Return list of pages."""
        pages = []

        for i in range(amount):
            movie_id = movies['results'][i]['id']
            movie = await self.get_movie(client, movie_id)

            page, img = await self.create_page(movie)
            pages.append((page, img))

        return pages

    async def get_movie(self, client: ClientSession, movie: int) -> Dict:
        """Get Movie by movie ID from TMDB. Return result dictionary."""
        url = BASE_URL + f"movie/{movie}?" + urlencode(MOVIE_PARAMS)

        async with client.get(url) as resp:
            return await resp.json()

    async def create_page(self, movie: Dict[str, Any]) -> Tuple[str, str]:
        """Create page from TMDB movie request result. Return formatted page + image."""
        text = ""

        # Add title + tagline (if not empty)
        text += f"**{movie['title']}**\n"
        if movie['tagline']:
            text += f"{movie['tagline']}\n\n"
        else:
            text += "\n"

        # Add other information
        text += f"**Rating:** {movie['vote_average']}/10 :star:\n"
        text += f"**Release Date:** {movie['release_date']}\n\n"

        text += "__**Production Information**__\n"

        companies = movie['production_companies']
        countries = movie['production_countries']

        text += f"**Made by:** {', '.join(company['name'] for company in companies)}\n"
        text += f"**Made in:** {', '.join(country['name'] for country in countries)}\n\n"

        text += "__**Some Numbers**__\n"

        text += f"**Budget:** ${movie['budget'] if movie['budget'] else '?'}\n"
        text += f"**Revenue:** ${movie['revenue'] if movie['revenue'] else '?'}\n"
        text += f"**Duration:** {movie['runtime']} minutes\n\n"

        text += movie['overview']

        img = f"http://image.tmdb.org/t/p/w200{movie['poster_path']}"

        # Return page content and image
        return text, img

    async def get_embed(self, name: str) -> Embed:
        """Return embed of random movies. Uses name in title."""
        return Embed(title=f'Random {name} Movies').set_footer(text='Powered by TMDB (themoviedb.org)')


def setup(bot: Bot) -> None:
    """Load Movie Cog."""
    bot.add_cog(Movie(bot))

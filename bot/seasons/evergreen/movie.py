import logging
import random
from enum import Enum
from os import environ
from typing import List, Tuple
from urllib.parse import urlencode

from aiohttp import ClientSession
from discord import Embed
from discord.ext.commands import Bot, Cog, Context, command

from bot.pagination import ImagePaginator

# Get TMDB API key from .env
TMDB_API_KEY = environ.get('TMDB_API_KEY')

# Define base URL of TMDB
BASE_URL = "https://api.themoviedb.org/3/"

# Get logger
logger = logging.getLogger(__name__)


# Genres with TMDB API IDs
class MovieGenres(Enum):
    """Genre names and IDs."""

    Action = 28
    Adventure = 12
    Animation = 16
    Comedy = 35
    Crime = 80
    Documentary = 99
    Drama = 18
    Family = 10751
    Fantasy = 14
    History = 36
    Horror = 27
    Music = 10402
    Mystery = 9648
    Romance = 10749
    Science = 878
    Thriller = 53
    Western = 37


async def get_random_movies(client: ClientSession,
                            count: int,
                            genre_id: int,
                            genre_name: str,) \
        -> Tuple[List[Tuple[str, str]], Embed]:
    """Get random movies by genre from TMDB."""
    pages = []

    # Create embed
    embed = Embed(title=f"Random {genre_name} Movies")
    embed.set_footer(text='Powered by TMDB (themoviedb.org)')

    # Get random page between 1 and 200
    page = random.randint(1, 200)

    # Define TMDB request parameters
    # (API key, exclusions, inclusions, sort)
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "sort_by": "popularity.desc",
        "include_adult": "false",
        "include_video": "false",
        "page": page,
        "with_genres": str(genre_id)
    }

    # Create request URL
    url = BASE_URL + "discover/movie" + "?" + urlencode(params)

    # Do discover request to TMDB API and fetch information
    async with client.get(url) as res:
        try:
            # Parse response data from JSON to dictionary
            movie_list_data = await res.json()

            # Loop and fetch movies
            for i in range(count):
                # Get movie ID
                movie_id = movie_list_data["results"][i]["id"]

                # Create movie params
                movie_params = {
                    "api_key": TMDB_API_KEY,
                    "language": "en-US"
                }

                # Generate URL
                movie_url = BASE_URL + f"movie/{movie_id}?" + urlencode(
                    movie_params)

                # Fetch movie
                async with client.get(movie_url) as m_res:
                    # Parse JSON to dict
                    movie_data = await m_res.json()

                    # Create embed text
                    movie_text = ""

                    # Add Title and tagline
                    movie_text += f"**{movie_data['title']}**\n"
                    if movie_data['tagline'] != "":
                        movie_text += movie_data['tagline'] + "\n\n"
                    else:
                        movie_text += "\n"

                    # Add movie rating and release date
                    movie_text += f"**Rating:** {movie_data['vote_average']}/10 :star:\n"
                    movie_text += f"**Release Date:** {movie_data['release_date']}\n\n"

                    # Add production title
                    movie_text += "__**Production Information**__\n"

                    companies = movie_data['production_companies']
                    countries = movie_data['production_countries']

                    # Add production information
                    movie_text += f"""**Made by:** {', '.join([comp['name']
                                                               for comp in companies])}\n"""
                    movie_text += f"""**Made in:** {', '.join([country['name']
                                                               for country in countries])}\n\n"""

                    # Add Some Numbers title
                    movie_text += "__**Some Numbers**__\n"

                    # Add Budget, Revenue and Duration
                    movie_text += f"**Budget:** ${movie_data['budget'] if movie_data['budget'] != 0 else '?'}\n"
                    movie_text += f"**Revenue:** ${movie_data['revenue'] if movie_data['revenue'] != 0 else '?'}\n"
                    movie_text += f"**Duration:** {movie_data['runtime']} minutes\n\n"

                    # Add description
                    movie_text += movie_data['overview']

                    # Define Movie Image URL
                    movie_img_url = f"http://image.tmdb.org/t/p/w200{movie_data['poster_path']}"

                    # Append this page to pages
                    pages.append((movie_text, movie_img_url))
        except KeyError as err:
            # Create error message
            msg = f"There was KeyError while executing HTTP request. API may " \
                f"down or API key may be incorrect, however, some movies " \
                f"have some missing fields, and this error will raise this " \
                f"too. Problematic Key: \n```{err}``` "

            # Create error embed
            err_embed = Embed(title=":no_entry: Error :no_entry:")

            # Log error
            logger.warning(msg)

            # Return error message + embed
            return [(msg, "")], err_embed

    # Return all movies pages
    return pages, embed


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
            await ctx.send('You can\'t get more than 20 movies at once. (TMDB limits)')
            return
        elif amount < 1:
            await ctx.send('You can\'t get less than 1 movies. Just logic.')
            return

        # Capitalize genre for getting data from Enum
        genre = genre.capitalize()

        # Try to fetch pages and embed, when invalid genre, show help
        try:
            pages, embed = await get_random_movies(self.http_session, amount, MovieGenres[genre].value, genre)
        except KeyError:
            await ctx.send_help('movies')
            return

        # Send movies, paginate
        await ImagePaginator.paginate(pages, ctx, embed)


def setup(bot: Bot) -> None:
    """Load Movie Cog."""
    bot.add_cog(Movie(bot))

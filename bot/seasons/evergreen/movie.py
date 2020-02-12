import logging
import random
from os import environ
from typing import List, Tuple
from urllib.parse import urlencode

from aiohttp import ClientSession
from discord import Embed
from discord.ext.commands import Bot, Cog, Context, group

from bot.pagination import ImagePaginator

# Get TMDB API key from .env
TMDB_API_KEY = environ.get('TMDB_API_KEY')

# Define base URL of TMDB
BASE_URL = "https://api.themoviedb.org/3/"

# Get logger
logger = logging.getLogger(__name__)


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

    # Get random page between 1 and 600
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

    @group(name='movies', invoke_without_command=True)
    async def movies(self, ctx: Context) -> None:
        """Get random movies by specifing genre."""
        await ctx.send_help('movies')

    @movies.command(name='action')
    async def action(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Action genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 28, "Action")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='adventure')
    async def adventure(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Adventure genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 12, "Adventure")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='animation')
    async def animation(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Animation genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 16, "Animation")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='comedy')
    async def comedy(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Comedy genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 35, "Comedy")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='crime')
    async def crime(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Crime genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 80, "Crime")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='documentary')
    async def documentary(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Documentary genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 99, "Documentary")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='drama')
    async def drama(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Drama genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 18, "Drama")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='family')
    async def family(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Drama genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 10751, "Family")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='fantasy')
    async def fantasy(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Fantasy genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 14, "Fantasy")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='history')
    async def history(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random History genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 36, "History")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='horror')
    async def horror(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Horror genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 27, "Horror")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='music')
    async def music(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Music genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 10402, "Music")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='mystery')
    async def mystery(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Mystery genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 9648, "Mystery")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='romance')
    async def romance(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Romance genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 10749, "Romance")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='science')
    async def science(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Science Fiction genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 878, "Science Fiction")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='thriller')
    async def thriller(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Thriller genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 53,
                                               "Thriller")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name='western')
    async def western(self, ctx: Context, movies_amount: int = 5) -> None:
        """Get random Western genre movies."""
        # Count can't be higher than 20, due one page return 20 items
        # And also this can't be lower than 1, just logic
        if movies_amount > 20:
            await ctx.send("Max allowed amount of movies is 20.")
            return
        elif movies_amount < 1:
            await ctx.send("You can't get less movies than 1.")
            return

        # Get pages and embed
        pages, embed = await get_random_movies(self.http_session,
                                               movies_amount, 37,
                                               "Western")

        # Paginate
        await ImagePaginator.paginate(pages, ctx, embed)


def setup(bot: Bot) -> None:
    """Load Movie Cog."""
    bot.add_cog(Movie(bot))

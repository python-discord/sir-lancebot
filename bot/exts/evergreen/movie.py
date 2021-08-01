import logging
import random
from enum import Enum
from typing import Any, Dict, List, Tuple
from urllib.parse import urlencode

from aiohttp import ClientSession
from discord import Embed
from discord.ext.commands import Cog, Context, group

from bot.bot import Bot
from bot.constants import Tokens
from bot.utils.extensions import invoke_help_command
from bot.utils.pagination import ImagePaginator

# Define base URL of TMDB
BASE_URL = "https://api.themoviedb.org/3/"

logger = logging.getLogger(__name__)

# Define movie params, that will be used for every movie request
MOVIE_PARAMS = {
    "api_key": Tokens.tmdb,
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
        self.http_session: ClientSession = bot.http_session

    @group(name="movies", aliases=("movie",), invoke_without_command=True)
    async def movies(self, ctx: Context, genre: str = "", amount: int = 5) -> None:
        """
        Get random movies by specifying genre. Also support amount parameter, that define how much movies will be shown.

        Default 5. Use .movies genres to get all available genres.
        """
        # Check is there more than 20 movies specified, due TMDB return 20 movies
        # per page, so this is max. Also you can't get less movies than 1, just logic
        if amount > 20:
            await ctx.send("You can't get more than 20 movies at once. (TMDB limits)")
            return
        elif amount < 1:
            await ctx.send("You can't get less than 1 movie.")
            return

        # Capitalize genre for getting data from Enum, get random page, send help when genre don't exist.
        genre = genre.capitalize()
        try:
            result = await self.get_movies_data(self.http_session, MovieGenres[genre].value, 1)
        except KeyError:
            await invoke_help_command(ctx)
            return

        # Check if "results" is in result. If not, throw error.
        if "results" not in result:
            err_msg = (
                f"There is problem while making TMDB API request. Response Code: {result['status_code']}, "
                f"{result['status_message']}."
            )
            await ctx.send(err_msg)
            logger.warning(err_msg)

        # Get random page. Max page is last page where is movies with this genre.
        page = random.randint(1, result["total_pages"])

        # Get movies list from TMDB, check if results key in result. When not, raise error.
        movies = await self.get_movies_data(self.http_session, MovieGenres[genre].value, page)
        if "results" not in movies:
            err_msg = f"There is problem while making TMDB API request. Response Code: {result['status_code']}, " \
                      f"{result['status_message']}."
            await ctx.send(err_msg)
            logger.warning(err_msg)

        # Get all pages and embed
        pages = await self.get_pages(self.http_session, movies, amount)
        embed = await self.get_embed(genre)

        await ImagePaginator.paginate(pages, ctx, embed)

    @movies.command(name="genres", aliases=("genre", "g"))
    async def genres(self, ctx: Context) -> None:
        """Show all currently available genres for .movies command."""
        await ctx.send(f"Current available genres: {', '.join('`' + genre.name + '`' for genre in MovieGenres)}")

    async def get_movies_data(self, client: ClientSession, genre_id: str, page: int) -> List[Dict[str, Any]]:
        """Return JSON of TMDB discover request."""
        # Define params of request
        params = {
            "api_key": Tokens.tmdb,
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
            movie_id = movies["results"][i]["id"]
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
        if movie["tagline"]:
            text += f"{movie['tagline']}\n\n"
        else:
            text += "\n"

        # Add other information
        text += f"**Rating:** {movie['vote_average']}/10 :star:\n"
        text += f"**Release Date:** {movie['release_date']}\n\n"

        text += "__**Production Information**__\n"

        companies = movie["production_companies"]
        countries = movie["production_countries"]

        text += f"**Made by:** {', '.join(company['name'] for company in companies)}\n"
        text += f"**Made in:** {', '.join(country['name'] for country in countries)}\n\n"

        text += "__**Some Numbers**__\n"

        budget = f"{movie['budget']:,d}" if movie['budget'] else "?"
        revenue = f"{movie['revenue']:,d}" if movie['revenue'] else "?"

        if movie["runtime"] is not None:
            duration = divmod(movie["runtime"], 60)
        else:
            duration = ("?", "?")

        text += f"**Budget:** ${budget}\n"
        text += f"**Revenue:** ${revenue}\n"
        text += f"**Duration:** {f'{duration[0]} hour(s) {duration[1]} minute(s)'}\n\n"

        text += movie["overview"]

        img = f"http://image.tmdb.org/t/p/w200{movie['poster_path']}"

        # Return page content and image
        return text, img

    async def get_embed(self, name: str) -> Embed:
        """Return embed of random movies. Uses name in title."""
        embed = Embed(title=f"Random {name} Movies")
        embed.set_footer(text="This product uses the TMDb API but is not endorsed or certified by TMDb.")
        embed.set_thumbnail(url="https://i.imgur.com/LtFtC8H.png")
        return embed


def setup(bot: Bot) -> None:
    """Load the Movie Cog."""
    bot.add_cog(Movie(bot))

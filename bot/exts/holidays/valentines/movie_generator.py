import random
from os import environ

import discord
from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.bot import Bot

TMDB_API_KEY = environ.get("TMDB_API_KEY")

log = get_logger(__name__)


class RomanceMovieFinder(commands.Cog):
    """A Cog that returns a random romance movie suggestion to a user."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="romancemovie")
    async def romance_movie(self, ctx: commands.Context) -> None:
        """Randomly selects a romance movie and displays information about it."""
        # Selecting a random int to parse it to the page parameter
        random_page = random.randint(0, 20)
        # TMDB api params
        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US",
            "sort_by": "popularity.desc",
            "include_adult": "false",
            "include_video": "false",
            "page": random_page,
            "with_genres": "10749"
        }
        # The api request url
        request_url = "https://api.themoviedb.org/3/discover/movie"
        async with self.bot.http_session.get(request_url, params=params) as resp:
            # Trying to load the json file returned from the api
            try:
                data = await resp.json()
                # Selecting random result from results object in the json file
                selected_movie = random.choice(data["results"])

                embed = discord.Embed(
                    title=f":sparkling_heart: {selected_movie['title']} :sparkling_heart:",
                    description=selected_movie["overview"],
                )
                embed.set_image(url=f"http://image.tmdb.org/t/p/w200/{selected_movie['poster_path']}")
                embed.add_field(name="Release date :clock1:", value=selected_movie["release_date"])
                embed.add_field(name="Rating :star2:", value=selected_movie["vote_average"])
                embed.set_footer(text="This product uses the TMDb API but is not endorsed or certified by TMDb.")
                embed.set_thumbnail(url="https://i.imgur.com/LtFtC8H.png")
                await ctx.send(embed=embed)
            except KeyError:
                warning_message = (
                    "A KeyError was raised while fetching information on the movie. The API service"
                    " could be unavailable or the API key could be set incorrectly."
                )
                embed = discord.Embed(title=warning_message)
                log.warning(warning_message)
                await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the Romance movie Cog."""
    await bot.add_cog(RomanceMovieFinder(bot))

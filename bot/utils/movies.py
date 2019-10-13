import logging
import random
from os import environ
from urllib import parse

import discord
from discord.ext import commands

TMDB_API_KEY = environ.get("TMDB_API_KEY")

log = logging.getLogger(__name__)


async def send_random_movie_embed(bot: commands.Bot, ctx: commands.Context, pages: int = 1, icon: str = '',
                                  genre_code: str = None, keyword_code: str = None) -> None:
    """Randomly selects a movie and sends an embed with its details."""
    # Selecting a random int to parse it to the page parameter
    random_page = random.randint(0, pages)
    # TMDB api params
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "sort_by": "popularity.desc",
        "include_adult": "false",
        "include_video": "false",
        "page": random_page
    }
    if genre_code:
        params["with_genres"] = genre_code
    if keyword_code:
        params["with_keywords"] = keyword_code
    # The api request url
    request_url = "https://api.themoviedb.org/3/discover/movie?" + parse.urlencode(params)
    async with bot.http_session.get(request_url) as resp:
        # Trying to load the json file returned from the api
        try:
            data = await resp.json()
            # Selecting random result from results object in the json file
            selected_movie = random.choice(data["results"])

            embed = discord.Embed(
                title=f"{icon} {selected_movie['title']} {icon}",
                description=selected_movie["overview"],
            )
            embed.set_image(url=f"http://image.tmdb.org/t/p/w200/{selected_movie['poster_path']}")
            embed.add_field(name="Release date :clock1:", value=selected_movie["release_date"])
            embed.add_field(name="Rating :star2:", value=selected_movie["vote_average"])
            await ctx.send(embed=embed)
        except KeyError:
            warning_message = "A KeyError was raised while fetching information on the movie. The API service" \
                              " could be unavailable or the API key could be set incorrectly."
            embed = discord.Embed(title=warning_message)
            log.warning(warning_message)
            await ctx.send(embed=embed)

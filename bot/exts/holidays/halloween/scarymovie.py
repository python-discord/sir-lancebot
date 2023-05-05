import logging
import random

from discord import Embed
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES, Tokens

log = logging.getLogger(__name__)


class ScaryMovie(commands.Cog):
    """Selects a random scary movie and embeds info into Discord chat."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="scarymovie", alias=["smovie"])
    async def random_movie(self, ctx: commands.Context) -> None:
        """Randomly select a scary movie and display information about it."""
        async with ctx.typing():
            selection = await self.select_movie()
            if not selection:
                await ctx.send(embed=Embed(
                    title=random.choice(NEGATIVE_REPLIES),
                    description=":warning: Failed to select a movie from the API",
                    color=Colours.soft_red
                ))
                return
            movie_details = await self.format_metadata(selection)

        await ctx.send(embed=movie_details)

    async def select_movie(self) -> dict:
        """Selects a random movie and returns a JSON of movie details from TMDb."""
        url = "https://api.themoviedb.org/3/discover/movie"
        params = {
            "api_key": Tokens.tmdb.get_secret_value(),
            "with_genres": "27",
            "vote_count.gte": "5",
            "include_adult": "false"
        }
        headers = {
            "Content-Type": "application/json;charset=utf-8"
        }

        # Get total page count of horror movies
        async with self.bot.http_session.get(url=url, params=params, headers=headers) as response:
            data = await response.json()
            total_pages = data.get("total_pages")

        # Get movie details from one random result on a random page
        params["page"] = random.randint(1, min(total_pages, 500))
        async with self.bot.http_session.get(url=url, params=params, headers=headers) as response:
            data = await response.json()
            if (results := data.get("results")) is None:
                log.warning("Failed to select a movie - data returned from API has no 'results' key")
                return {}
            selection_id = random.choice(results).get("id")
            if selection_id is None:
                log.warning("Failed to select a movie - selected film didn't have an id")
                return {}

        # Get full details and credits
        async with self.bot.http_session.get(
            url=f"https://api.themoviedb.org/3/movie/{selection_id}",
            params={"api_key": Tokens.tmdb.get_secret_value(), "append_to_response": "credits"}
        ) as selection:

            return await selection.json()

    @staticmethod
    async def format_metadata(movie: dict) -> Embed:
        """Formats raw TMDb data to be embedded in Discord chat."""
        # Build the relevant URLs.
        movie_id = movie.get("id")
        poster_path = movie.get("poster_path")
        tmdb_url = f"https://www.themoviedb.org/movie/{movie_id}" if movie_id else None
        poster = f"https://image.tmdb.org/t/p/original{poster_path}" if poster_path else None

        # Get cast names
        cast = []
        for actor in movie.get("credits", {}).get("cast", [])[:3]:
            cast.append(actor.get("name"))

        # Get director name
        director = movie.get("credits", {}).get("crew", [])
        if director:
            director = director[0].get("name")

        # Determine the spookiness rating
        rating = ""
        rating_count = movie.get("vote_average", 0) / 2

        for _ in range(int(rating_count)):
            rating += ":skull:"
        if (rating_count % 1) >= .5:
            rating += ":bat:"

        # Try to get year of release and runtime
        year = movie.get("release_date", [])[:4]
        runtime = movie.get("runtime")
        runtime = f"{runtime} minutes" if runtime else None

        # Not all these attributes will always be present
        movie_attributes = {
            "Directed by": director,
            "Starring": ", ".join(cast),
            "Running time": runtime,
            "Release year": year,
            "Spookiness rating": rating,
        }

        embed = Embed(
            colour=0x01d277,
            title=f"**{movie.get('title')}**",
            url=tmdb_url,
            description=movie.get("overview")
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


async def setup(bot: Bot) -> None:
    """Load the Scary Movie Cog."""
    await bot.add_cog(ScaryMovie(bot))

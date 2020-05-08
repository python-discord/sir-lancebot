import difflib
import logging
import random
from datetime import datetime as dt
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple

from aiohttp import ClientSession
from discord import Embed
from discord.ext import tasks
from discord.ext.commands import Cog, Context, group

from bot.bot import SeasonalBot
from bot.constants import STAFF_ROLES, Tokens
from bot.decorators import with_role
from bot.pagination import ImagePaginator, LinePaginator

# Base URL of IGDB API
BASE_URL = "https://api-v3.igdb.com"

HEADERS = {
    "user-key": Tokens.igdb,
    "Accept": "application/json"
}

logger = logging.getLogger(__name__)

# ---------
# TEMPLATES
# ---------

# Body templates
# Request body template for get_games_list
GAMES_LIST_BODY = (
    "fields cover.image_id, first_release_date, total_rating, name, storyline, url, platforms.name, status,"
    "involved_companies.company.name, summary, age_ratings.category, age_ratings.rating, total_rating_count;"
    "{sort} {limit} {offset} {genre} {additional}"
)

# Request body template for get_companies_list
COMPANIES_LIST_BODY = (
    "fields name, url, start_date, logo.image_id, developed.name, published.name, description;"
    "offset {offset}; limit {limit};"
)

# Request body template for games search
SEARCH_BODY = 'fields name, url, storyline, total_rating, total_rating_count; limit 50; search "{term}";'

# Pages templates
# Game embed layout
GAME_PAGE = (
    "**[{name}]({url})**\n"
    "{description}"
    "**Release Date:** {release_date}\n"
    "**Rating:** {rating}/100 :star: (based on {rating_count} ratings)\n"
    "**Platforms:** {platforms}\n"
    "**Status:** {status}\n"
    "**Age Ratings:** {age_ratings}\n"
    "**Made by:** {made_by}\n\n"
    "{storyline}"
)

# .games company command page layout
COMPANY_PAGE = (
    "**[{name}]({url})**\n"
    "{description}"
    "**Founded:** {founded}\n"
    "**Developed:** {developed}\n"
    "**Published:** {published}"
)

# For .games search command line layout
GAME_SEARCH_LINE = (
    "**[{name}]({url})**\n"
    "{rating}/100 :star: (based on {rating_count} ratings)\n"
)

# URL templates
COVER_URL = "https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.jpg"
LOGO_URL = "https://images.igdb.com/igdb/image/upload/t_logo_med/{image_id}.png"

# Create aliases for complex genre names
ALIASES = {
    "Role-playing (rpg)": ["Role playing", "Rpg"],
    "Turn-based strategy (tbs)": ["Turn based strategy", "Tbs"],
    "Real time strategy (rts)": ["Real time strategy", "Rts"],
    "Hack and slash/beat 'em up": ["Hack and slash"]
}


class GameStatus(IntEnum):
    """Game statuses in IGDB API."""

    Released = 0
    Alpha = 2
    Beta = 3
    Early = 4
    Offline = 5
    Cancelled = 6
    Rumored = 7


class AgeRatingCategories(IntEnum):
    """IGDB API Age Rating categories IDs."""

    ESRB = 1
    PEGI = 2


class AgeRatings(IntEnum):
    """PEGI/ESRB ratings IGDB API IDs."""

    Three = 1
    Seven = 2
    Twelve = 3
    Sixteen = 4
    Eighteen = 5
    RP = 6
    EC = 7
    E = 8
    E10 = 9
    T = 10
    M = 11
    AO = 12


class Games(Cog):
    """Games Cog contains commands that collect data from IGDB."""

    def __init__(self, bot: SeasonalBot):
        self.bot = bot
        self.http_session: ClientSession = bot.http_session

        self.genres: Dict[str, int] = {}

        self.refresh_genres_task.start()

    @tasks.loop(hours=1.0)
    async def refresh_genres_task(self) -> None:
        """Refresh genres in every hour."""
        try:
            await self._get_genres()
        except Exception as e:
            logger.warning(f"There was error while refreshing genres: {e}")
            return
        logger.info("Successfully refreshed genres.")

    def cog_unload(self) -> None:
        """Cancel genres refreshing start when unloading Cog."""
        self.refresh_genres_task.cancel()
        logger.info("Successfully stopped Genres Refreshing task.")

    async def _get_genres(self) -> None:
        """Create genres variable for games command."""
        body = "fields name; limit 100;"
        async with self.http_session.get(f"{BASE_URL}/genres", data=body, headers=HEADERS) as resp:
            result = await resp.json()

        genres = {genre["name"].capitalize(): genre["id"] for genre in result}

        # Replace complex names with names from ALIASES
        for genre_name, genre in genres.items():
            if genre_name in ALIASES:
                for alias in ALIASES[genre_name]:
                    self.genres[alias] = genre
            else:
                self.genres[genre_name] = genre

    @group(name="games", aliases=["game"], invoke_without_command=True)
    async def games(self, ctx: Context, amount: Optional[int] = 5, *, genre: Optional[str] = None) -> None:
        """
        Get random game(s) by genre from IGDB. Use .games genres command to get all available genres.

        Also support amount parameter, what max is 25 and min 1, default 5. Supported formats:
        - .games <genre>
        - .games <amount> <genre>
        """
        # When user didn't specified genre, send help message
        if genre is None:
            await ctx.send_help("games")
            return

        # Capitalize genre for check
        genre = "".join(genre).capitalize()

        # Check for amounts, max is 25 and min 1
        if not 1 <= amount <= 25:
            await ctx.send("Your provided amount is out of range. Our minimum is 1 and maximum 25.")
            return

        # Get games listing, if genre don't exist, show error message with possibilities.
        # Offset must be random, due otherwise we will get always same result (offset show in which position should
        # API start returning result)
        try:
            games = await self.get_games_list(amount, self.genres[genre], offset=random.randint(0, 150))
        except KeyError:
            possibilities = "`, `".join(difflib.get_close_matches(genre, self.genres))
            await ctx.send(f"Invalid genre `{genre}`. {f'Maybe you meant `{possibilities}`?' if possibilities else ''}")
            return

        # Create pages and paginate
        pages = [await self.create_page(game) for game in games]

        await ImagePaginator.paginate(pages, ctx, Embed(title=f"Random {genre.title()} Games"))

    @games.command(name="top", aliases=["t"])
    async def top(self, ctx: Context, amount: int = 10) -> None:
        """
        Get current Top games in IGDB.

        Support amount parameter. Max is 25, min is 1.
        """
        if not 1 <= amount <= 25:
            await ctx.send("Your provided amount is out of range. Our minimum is 1 and maximum 25.")
            return

        games = await self.get_games_list(amount, sort="total_rating desc",
                                          additional_body="where total_rating >= 90; sort total_rating_count desc;")

        pages = [await self.create_page(game) for game in games]
        await ImagePaginator.paginate(pages, ctx, Embed(title=f"Top {amount} Games"))

    @games.command(name="genres", aliases=["genre", "g"])
    async def genres(self, ctx: Context) -> None:
        """Get all available genres."""
        await ctx.send(f"Currently available genres: {', '.join(f'`{genre}`' for genre in self.genres)}")

    @games.command(name="search", aliases=["s"])
    async def search(self, ctx: Context, *, search_term: str) -> None:
        """Find games by name."""
        lines = await self.search_games(search_term)

        await LinePaginator.paginate(lines, ctx, Embed(title=f"Game Search Results: {search_term}"), empty=False)

    @games.command(name="company", aliases=["companies"])
    async def company(self, ctx: Context, amount: int = 5) -> None:
        """
        Get random Game Companies companies from IGDB API.

        Support amount parameter. Max is 25, min is 1.
        """
        if not 1 <= amount <= 25:
            await ctx.send("Your provided amount is out of range. Our minimum is 1 and maximum 25.")
            return

        # Get companies listing. Provide limit for limiting how much companies will be returned. Get random offset to
        # get (almost) every time different companies (offset show in which position should API start returning result)
        companies = await self.get_companies_list(limit=amount, offset=random.randint(0, 150))
        pages = [await self.create_company_page(co) for co in companies]

        await ImagePaginator.paginate(pages, ctx, Embed(title="Random Game Companies"))

    @with_role(*STAFF_ROLES)
    @games.command(name="refresh", aliases=["r"])
    async def refresh_genres_command(self, ctx: Context) -> None:
        """Refresh .games command genres."""
        try:
            await self._get_genres()
        except Exception as e:
            await ctx.send(f"There was error while refreshing genres: `{e}`")
            return
        await ctx.send("Successfully refreshed genres.")

    async def get_games_list(self,
                             amount: int,
                             genre: Optional[str] = None,
                             sort: Optional[str] = None,
                             additional_body: str = "",
                             offset: int = 0
                             ) -> List[Dict[str, Any]]:
        """
        Get list of games from IGDB API by parameters that is provided.

        Amount param show how much games this get, genre is genre ID and at least one genre in game must this when
        provided. Sort is sorting by specific field and direction, ex. total_rating desc/asc (total_rating is field,
        desc/asc is direction). Additional_body is field where you can pass extra search parameters. Offset show start
        position in API.
        """
        # Create body of IGDB API request, define fields, sorting, offset, limit and genre
        params = {
            "sort": f"sort {sort};" if sort else "",
            "limit": f"limit {amount};",
            "offset": f"offset {offset};" if offset else "",
            "genre": f"where genres = ({genre});" if genre else "",
            "additional": additional_body
        }
        body = GAMES_LIST_BODY.format(**params)

        # Do request to IGDB API, create headers, URL, define body, return result
        async with self.http_session.get(url=f"{BASE_URL}/games", data=body, headers=HEADERS) as resp:
            return await resp.json()

    async def create_page(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """Create content of Game Page."""
        # Create cover image URL from template
        url = COVER_URL.format(**{"image_id": data["cover"]["image_id"] if "cover" in data else ""})

        # Get release date separately with checking
        release_date = dt.utcfromtimestamp(data["first_release_date"]).date() if "first_release_date" in data else "?"

        # Create Age Ratings value
        rating = ", ".join(f"{AgeRatingCategories(age['category']).name} {AgeRatings(age['rating']).name}"
                           for age in data["age_ratings"]) if "age_ratings" in data else "?"

        companies = [c["company"]["name"] for c in data["involved_companies"]] if "involved_companies" in data else "?"

        # Create formatting for template page
        formatting = {
            "name": data["name"],
            "url": data["url"],
            "description": f"{data['summary']}\n\n" if "summary" in data else "\n",
            "release_date": release_date,
            "rating": round(data["total_rating"] if "total_rating" in data else 0, 2),
            "rating_count": data["total_rating_count"] if "total_rating_count" in data else "?",
            "platforms": ", ".join(platform["name"] for platform in data["platforms"]) if "platforms" in data else "?",
            "status": GameStatus(data["status"]).name if "status" in data else "?",
            "age_ratings": rating,
            "made_by": ", ".join(companies),
            "storyline": data["storyline"] if "storyline" in data else ""
        }
        page = GAME_PAGE.format(**formatting)

        return page, url

    async def search_games(self, search_term: str) -> List[str]:
        """Search game from IGDB API by string, return listing of pages."""
        lines = []

        # Define request body of IGDB API request and do request
        body = SEARCH_BODY.format(**{"term": search_term})

        async with self.http_session.get(url=f"{BASE_URL}/games", data=body, headers=HEADERS) as resp:
            data = await resp.json()

        # Loop over games, format them to good format, make line and append this to total lines
        for game in data:
            formatting = {
                "name": game["name"],
                "url": game["url"],
                "rating": round(game["total_rating"] if "total_rating" in game else 0, 2),
                "rating_count": game["total_rating_count"] if "total_rating" in game else "?"
            }
            line = GAME_SEARCH_LINE.format(**formatting)
            lines.append(line)

        return lines

    async def get_companies_list(self, limit: int, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get random Game Companies from IGDB API.

        Limit is parameter, that show how much movies this should return, offset show in which position should API start
        returning results.
        """
        # Create request body from template
        body = COMPANIES_LIST_BODY.format(**{
            "limit": limit,
            "offset": offset
        })

        async with self.http_session.get(url=f"{BASE_URL}/companies", data=body, headers=HEADERS) as resp:
            return await resp.json()

    async def create_company_page(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """Create good formatted Game Company page."""
        # Generate URL of company logo
        url = LOGO_URL.format(**{"image_id": data["logo"]["image_id"] if "logo" in data else ""})

        # Try to get found date of company
        founded = dt.utcfromtimestamp(data["start_date"]).date() if "start_date" in data else "?"

        # Generate list of games, that company have developed or published
        developed = ", ".join(game["name"] for game in data["developed"]) if "developed" in data else "?"
        published = ", ".join(game["name"] for game in data["published"]) if "published" in data else "?"

        formatting = {
            "name": data["name"],
            "url": data["url"],
            "description": f"{data['description']}\n\n" if "description" in data else "\n",
            "founded": founded,
            "developed": developed,
            "published": published
        }
        page = COMPANY_PAGE.format(**formatting)

        return page, url


def setup(bot: SeasonalBot) -> None:
    """Add/Load Games cog."""
    # Check does IGDB API key exist, if not, log warning and don't load cog
    if not Tokens.igdb:
        logger.warning("No IGDB API key. Not loading Games cog.")
        return
    bot.add_cog(Games(bot))

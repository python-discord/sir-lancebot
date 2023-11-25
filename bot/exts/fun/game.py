import difflib
import random
import re
from datetime import UTC, datetime, timedelta
from enum import IntEnum
from typing import Any

from aiohttp import ClientSession
from discord import Embed
from discord.ext import tasks
from discord.ext.commands import Cog, Context, group
from pydis_core.utils import scheduling
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import STAFF_ROLES, Tokens
from bot.utils.decorators import with_role
from bot.utils.pagination import ImagePaginator, LinePaginator

# Base URL of IGDB API
BASE_URL = "https://api.igdb.com/v4"

CLIENT_ID = Tokens.igdb_client_id.get_secret_value()
CLIENT_SECRET = Tokens.igdb_client_secret.get_secret_value()

# The number of seconds before expiry that we attempt to re-fetch a new access token
ACCESS_TOKEN_RENEWAL_WINDOW = 60*60*24*2

# URL to request API access token
OAUTH_URL = "https://id.twitch.tv/oauth2/token"

OAUTH_PARAMS = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type": "client_credentials"
}

BASE_HEADERS = {
    "Client-ID": CLIENT_ID,
    "Accept": "application/json"
}

logger = get_logger(__name__)

REGEX_NON_ALPHABET = re.compile(r"[^a-z0-9]", re.IGNORECASE)

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
    Delisted = 8


class AgeRatingCategories(IntEnum):
    """IGDB API Age Rating categories IDs."""

    ESRB = 1
    PEGI = 2
    CERO = 3
    USK = 4
    GRAC = 5
    CLASS_IND = 6
    ACB = 7


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
    CERO_A = 13
    CERO_B = 14
    CERO_C = 15
    CERO_D = 16
    CERO_Z = 17
    USK_0 = 18
    USK_6 = 19
    USK_12 = 20
    USK_18 = 21
    GRAC_ALL = 22
    GRAC_Twelve = 23
    GRAC_Fifteen = 24
    GRAC_Eighteen = 25
    GRAC_TESTING = 26
    CLASS_IND_L = 27
    CLASS_IND_Ten = 28
    CLASS_IND_Twelve = 29
    CLASS_IND_Fourteen = 30
    CLASS_IND_Sixteen = 31
    CLASS_IND_Eighteen = 32
    ACB_G = 33
    ACB_PG = 34
    ACB_M = 35
    ACB_MA15 = 36
    ACB_R18 = 37
    ACB_RC = 38


class Games(Cog):
    """Games Cog contains commands that collect data from IGDB."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.http_session: ClientSession = bot.http_session

        self.genres: dict[str, int] = {}
        self.headers = BASE_HEADERS
        self.token_refresh_scheduler = scheduling.Scheduler(__name__)

    async def cog_load(self) -> None:
        """Get an auth token and start the refresh task on cog load."""
        await self.refresh_token()
        self.refresh_genres_task.start()

    async def refresh_token(self) -> None:
        """
        Refresh the IGDB V4 access token.

        Once a new token has been created, schedule another refresh `ACCESS_TOKEN_RENEWAL_WINDOW` seconds before expiry.
        """
        async with self.http_session.post(OAUTH_URL, params=OAUTH_PARAMS) as resp:
            result = await resp.json()
            if resp.status != 200:
                # If there is a valid access token continue to use that,
                # otherwise unload cog.
                if "Authorization" in self.headers:
                    time_delta = timedelta(seconds=ACCESS_TOKEN_RENEWAL_WINDOW)
                    logger.error(
                        "Failed to renew IGDB access token. "
                        f"Current token will last for {time_delta} "
                        f"OAuth response message: {result['message']}"
                    )
                else:
                    logger.warning(
                        "Invalid OAuth credentials. Unloading Games cog. "
                        f"OAuth response message: {result['message']}"
                    )
                    self.bot.remove_cog("Games")
                return

        self.headers["Authorization"] = f"Bearer {result['access_token']}"

        # Attempt to renew before the token expires
        seconds_until_next_renewal = result["expires_in"] - ACCESS_TOKEN_RENEWAL_WINDOW
        logger.info(f"Successfully renewed access token. Refreshing again in {seconds_until_next_renewal} seconds")
        self.token_refresh_scheduler.schedule_later(seconds_until_next_renewal, __name__, self.refresh_token())

    @tasks.loop(hours=24.0)
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
        async with self.http_session.post(f"{BASE_URL}/genres", data=body, headers=self.headers) as resp:
            result = await resp.json()
        genres = {genre["name"].capitalize(): genre["id"] for genre in result}

        # Replace complex names with names from ALIASES
        for genre_name, genre in genres.items():
            if genre_name in ALIASES:
                for alias in ALIASES[genre_name]:
                    self.genres[alias] = genre
            else:
                self.genres[genre_name] = genre

    @group(name="games", aliases=("game",), invoke_without_command=True)
    async def games(self, ctx: Context, amount: int | None = 5, *, genre: str | None) -> None:
        """
        Get random game(s) by genre from IGDB. Use .games genres command to get all available genres.

        Also support amount parameter, what max is 25 and min 1, default 5. Supported formats:
        - .games <genre>
        - .games <amount> <genre>
        """
        # When user didn't specified genre, send help message
        if genre is None:
            await self.bot.invoke_help_command(ctx)
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
            possibilities = await self.get_best_results(genre)
            # If there is more than 1 possibilities, show these.
            # If there is only 1 possibility, use it as genre.
            # Otherwise send message about invalid genre.
            if len(possibilities) > 1:
                display_possibilities = "`, `".join(p[1] for p in possibilities)
                await ctx.send(
                    f"Invalid genre `{genre}`. "
                    f"{f'Maybe you meant `{display_possibilities}`?' if display_possibilities else ''}"
                )
                return

            if len(possibilities) == 1:
                games = await self.get_games_list(
                    amount, self.genres[possibilities[0][1]], offset=random.randint(0, 150)
                )
                genre = possibilities[0][1]
            else:
                await ctx.send(f"Invalid genre `{genre}`.")
                return

        # Create pages and paginate
        pages = [await self.create_page(game) for game in games]

        await ImagePaginator.paginate(pages, ctx, Embed(title=f"Random {genre.title()} Games"))

    @games.command(name="top", aliases=("t",))
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

    @games.command(name="genres", aliases=("genre", "g"))
    async def genres(self, ctx: Context) -> None:
        """Get all available genres."""
        await ctx.send(f"Currently available genres: {', '.join(f'`{genre}`' for genre in self.genres)}")

    @games.command(name="search", aliases=("s",))
    async def search(self, ctx: Context, *, search_term: str) -> None:
        """Find games by name."""
        lines = await self.search_games(search_term)

        await LinePaginator.paginate(lines, ctx, Embed(title=f"Game Search Results: {search_term}"), empty=False)

    @games.command(name="company", aliases=("companies",))
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
    @games.command(name="refresh", aliases=("r",))
    async def refresh_genres_command(self, ctx: Context) -> None:
        """Refresh .games command genres."""
        try:
            await self._get_genres()
        except Exception as e:
            await ctx.send(f"There was error while refreshing genres: `{e}`")
            return
        await ctx.send("Successfully refreshed genres.")

    async def get_games_list(
        self,
        amount: int,
        genre: str | None = None,
        sort: str | None = None,
        additional_body: str = "",
        offset: int = 0
    ) -> list[dict[str, Any]]:
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
        async with self.http_session.post(url=f"{BASE_URL}/games", data=body, headers=self.headers) as resp:
            return await resp.json()

    async def create_page(self, data: dict[str, Any]) -> tuple[str, str]:
        """Create content of Game Page."""
        # Create cover image URL from template
        url = COVER_URL.format(image_id=data.get("cover", {}).get("image_id", ""))

        # Get release date separately with checking
        if "first_release_date" in data:
            release_date = datetime.fromtimestamp(data["first_release_date"], tz=UTC).date()
        else:
            release_date = "?"

        # Create Age Ratings value
        rating = ", ".join(
            f"{AgeRatingCategories(age['category']).name} {AgeRatings(age['rating']).name}"
            for age in data["age_ratings"]
        ) if "age_ratings" in data else "?"

        companies = [c["company"]["name"] for c in data["involved_companies"]] if "involved_companies" in data else "?"

        # Create formatting for template page
        formatting = {
            "name": data["name"],
            "url": data["url"],
            "description": f"{data['summary']}\n\n" if "summary" in data else "\n",
            "release_date": release_date,
            "rating": round(data.get("total_rating", 0), 2),
            "rating_count": data.get("total_rating_count", "?"),
            "platforms": ", ".join(platform["name"] for platform in data["platforms"]) if "platforms" in data else "?",
            "status": GameStatus(data["status"]).name if "status" in data else "?",
            "age_ratings": rating,
            "made_by": ", ".join(companies),
            "storyline": data.get("storyline", "")
        }
        page = GAME_PAGE.format(**formatting)

        return page, url

    async def search_games(self, search_term: str) -> list[str]:
        """Search game from IGDB API by string, return listing of pages."""
        lines = []

        # Define request body of IGDB API request and do request
        body = SEARCH_BODY.format(term=search_term)

        async with self.http_session.post(url=f"{BASE_URL}/games", data=body, headers=self.headers) as resp:
            data = await resp.json()

        # Loop over games, format them to good format, make line and append this to total lines
        for game in data:
            formatting = {
                "name": game["name"],
                "url": game["url"],
                "rating": round(game.get("total_rating", 0), 2),
                "rating_count": game["total_rating_count"] if "total_rating" in game else "?"
            }
            line = GAME_SEARCH_LINE.format(**formatting)
            lines.append(line)

        return lines

    async def get_companies_list(self, limit: int, offset: int = 0) -> list[dict[str, Any]]:
        """
        Get random Game Companies from IGDB API.

        Limit is parameter, that show how much movies this should return, offset show in which position should API start
        returning results.
        """
        # Create request body from template
        body = COMPANIES_LIST_BODY.format(
            limit=limit,
            offset=offset,
        )

        async with self.http_session.post(url=f"{BASE_URL}/companies", data=body, headers=self.headers) as resp:
            return await resp.json()

    async def create_company_page(self, data: dict[str, Any]) -> tuple[str, str]:
        """Create good formatted Game Company page."""
        # Generate URL of company logo
        url = LOGO_URL.format(image_id=data.get("logo", {}).get("image_id", ""))

        # Try to get found date of company
        founded = datetime.fromtimestamp(data["start_date"], tz=UTC).date() if "start_date" in data else "?"

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

    async def get_best_results(self, query: str) -> list[tuple[float, str]]:
        """Get best match result of genre when original genre is invalid."""
        results = []
        for genre in self.genres:
            ratios = [difflib.SequenceMatcher(None, query, genre).ratio()]
            for word in REGEX_NON_ALPHABET.split(genre):
                ratios.append(difflib.SequenceMatcher(None, query, word).ratio())
            results.append((round(max(ratios), 2), genre))
        return sorted((item for item in results if item[0] >= 0.60), reverse=True)[:4]


async def setup(bot: Bot) -> None:
    """Load the Games cog."""
    # Check does IGDB API key exist, if not, log warning and don't load cog
    if not Tokens.igdb_client_id:
        logger.warning("No IGDB client ID. Not loading Games cog.")
        return
    if not Tokens.igdb_client_secret:
        logger.warning("No IGDB client secret. Not loading Games cog.")
        return
    await bot.add_cog(Games(bot))

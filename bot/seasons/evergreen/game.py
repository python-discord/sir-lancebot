import asyncio
import random
from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, List, Tuple

from aiohttp import ClientSession
from discord import Embed
from discord.ext.commands import Bot, Cog, Context, group

from bot.constants import Tokens
from bot.pagination import ImagePaginator, LinePaginator

# Base URL of IGDB API
BASE_URL = "https://api-v3.igdb.com/"
IMAGE_BASE_URL = "https://images.igdb.com/igdb/image/upload/"

HEADERS = {
    "user-key": Tokens.igdb,
    "Accept": "application/json"
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

    def __init__(self, bot: Bot):
        self.bot = bot
        self.http_session: ClientSession = bot.http_session

        # Initialize genres
        asyncio.get_event_loop().create_task(self._get_genres())

    async def _get_genres(self) -> None:
        """Create genres variable for games command."""
        body = "fields name; limit 100;"
        async with self.http_session.get(BASE_URL + "genres", data=body, headers=HEADERS) as resp:
            result = await resp.json()

        genres = {genre['name'].capitalize(): genre['id'] for genre in result}

        self.genres = {}

        # Manual check genres, replace sentences with words
        for genre in genres:
            if genre == "Role-playing (rpg)":
                self.genres["Role-playing"] = genres[genre]
                self.genres["Rpg"] = genres[genre]
            elif genre == "Turn-based strategy (tbs)":
                self.genres["Turn-based-strategy"] = genres[genre]
                self.genres["Tbs"] = genres[genre]
            elif genre == "Real time strategy (rts)":
                self.genres["Real-time-strategy"] = genres[genre]
                self.genres["Rts"] = genres[genre]
            elif genre == "Hack and slash/beat 'em up":
                self.genres["Hack-and-slash"] = genres[genre]
            else:
                self.genres[genre] = genres[genre]

    @group(name='games', aliases=['game'], invoke_without_command=True)
    async def games(self, ctx: Context, genre: str = "", amount: int = 5) -> None:
        """
        Get random game(s) by genre from IGDB. Use .movies genres command to get all available genres.

        Also support amount parameter, what max is 25 and min 1, default 5. Use quotes ("") for genres with multiple
        words.
        """
        # Capitalize genre for check
        genre = genre.capitalize()

        # Check for amounts, max is 25 and min 1
        if amount > 25:
            await ctx.send("You can't get more than 25 games at once.")
            return
        elif amount < 1:
            await ctx.send("You can't get less than 1 game.")
            return

        # Get games listing, if genre don't exist, show help.
        try:
            games = await self.get_games_list(self.http_session, amount, self.genres[genre],
                                              offset=random.randint(0, 150))
        except KeyError:
            await ctx.send_help('games')
            return

        # Create pages and paginate
        pages = [await self.create_page(game) for game in games]

        await ImagePaginator.paginate(pages, ctx, Embed(title=f'Random {genre} Games'))

    @games.command(name='top', aliases=['t'])
    async def top(self, ctx: Context, amount: int = 10) -> None:
        """
        Get current Top games in IGDB.

        Support amount parameter. Max is 25, min is 1.
        """
        if amount > 25:
            await ctx.send("You can't get more than top 25 games.")
            return
        elif amount < 1:
            await ctx.send("You can't get less than 1 top game.")
            return

        games = await self.get_games_list(self.http_session, amount, sort='total_rating desc',
                                          additional_body="where total_rating >= 90; sort total_rating_count desc;")

        pages = await self.get_pages(games)
        await ImagePaginator.paginate(pages, ctx, Embed(title=f'Top {amount} Games'))

    @games.command(name='genres', aliases=['genre', 'g'])
    async def genres(self, ctx: Context) -> None:
        """Get all available genres."""
        await ctx.send(f"Currently available genres: {', '.join(f'`{genre}`' for genre in self.genres)}")

    @games.command(name='search', aliases=['s'])
    async def search(self, ctx: Context, *, search: str) -> None:
        """Find games by name."""
        lines = await self.search_games(self.http_session, search)

        await LinePaginator.paginate((line for line in lines), ctx, Embed(title=f'Game Search Results: {search}'))

    @games.command(name='company', aliases=['companies'])
    async def company(self, ctx: Context, amount: int = 5) -> None:
        """
        Get random Game Companies companies from IGDB API.

        Support amount parameter. Max is 25, min is 1.
        """
        if amount > 25:
            await ctx.send("You can't get more than 25 companies at once.")
            return
        elif amount < 1:
            await ctx.send("You can't get less than 1 company.")
            return

        companies = await self.get_companies_list(self.http_session, amount, random.randint(0, 150))
        pages = [await self.create_company_page(co) for co in companies]

        await ImagePaginator.paginate(pages, ctx, Embed(title='Random Game Companies'))

    async def get_games_list(self,
                             client: ClientSession,
                             limit: int,
                             genre: str = None,
                             sort: str = None,
                             additional_body: str = "",
                             offset: int = 0) \
            -> List[Dict[str, Any]]:
        """Get Games List from IGDB API."""
        # Create body of IGDB API request, define fields, sorting, offset, limit and genre
        body = "fields cover.image_id, first_release_date, total_rating, name, storyline, url, platforms.name, "
        body += "status, involved_companies.company.name, summary, age_ratings.category, age_ratings.rating, "
        body += "total_rating_count;\n"

        body += f"sort {sort};\n" if sort else ''
        body += f"offset {offset};\n"
        body += f"limit {limit};\n"

        body += f"where genres = ({genre});" if genre else ''
        body += additional_body

        # Do request to IGDB API, create headers, URL, define body, return result
        async with client.get(
                url=BASE_URL + "games",
                data=body,
                headers=HEADERS
        ) as resp:
            return await resp.json()

    async def create_page(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """Create content of Game Page."""
        # Create page content variable, what will be returned
        page = ""

        # If game have cover, generate URL of Cover, if not, let url empty
        if 'cover' in data:
            url = f"{IMAGE_BASE_URL}t_cover_big/{data['cover']['image_id']}.jpg"
        else:
            url = ""

        # Add title with hyperlink and check for storyline
        page += f"**[{data['name']}]({data['url']})**\n"
        page += data['summary'] + "\n\n" if 'summary' in data else "\n"

        # Add release date if key is in game information
        if 'first_release_date' in data:
            page += f"**Release Date:** {datetime.utcfromtimestamp(data['first_release_date']).date()}\n"

        # Add other information
        page += f"**Rating:** {'{0:.2f}'.format(data['total_rating']) if 'total_rating' in data else '?'}/100 "
        page += f":star: (based on {data['total_rating_count'] if 'total_rating_count' in data else '?'})\n"

        page += f"**Platforms:** "
        page += f"{', '.join(pf['name'] for pf in data['platforms']) if 'platforms' in data else '?'}\n"

        page += f"**Status:** {GameStatus(data['status']).name if 'status' in data else '?'}\n"

        if 'age_ratings' in data:
            rating = ', '.join(f"{AgeRatingCategories(age['category']).name} {AgeRatings(age['rating']).name}"
                               for age in data['age_ratings'])
            page += f"**Age Ratings:** {rating}\n"

        if 'involved_companies' in data:
            companies = ', '.join(co['company']['name'] for co in data['involved_companies'])
        else:
            companies = "?"
        page += f"**Made by:** {companies}\n"

        page += "\n"
        page += data['storyline'] if 'storyline' in data else ''

        return page, url

    async def search_games(self, client: ClientSession, search: str) -> List[str]:
        """Search game from IGDB API by string, return listing of pages."""
        lines = []

        # Define request body of IGDB API request and do request
        body = f"""fields name, url, storyline, total_rating, total_rating_count;
search "{search}";
limit 50;"""

        async with client.get(
                url=BASE_URL + "games",
                data=body,
                headers=HEADERS) as resp:
            data = await resp.json()

        # Loop over games, format them to good format, make line and append this to total lines
        for game in data:
            line = ""

            # Add games name and rating, also attach URL to title
            line += f"**[{game['name']}]({game['url']})**\n"
            line += f"""{'{0:.2f}'.format(game['total_rating'] if 'total_rating' in game.keys() else 0)}/100 :star: (by {
            game['total_rating_count'] if 'total_rating_count' in game else '?'} users)"""

            lines.append(line)

        return lines

    async def get_companies_list(self, client: ClientSession, limit: int, offset: int = 0) -> List[Dict[str, Any]]:
        """Get random Game Companies from IGDB API."""
        # Create request body, define included fields, limit and offset, do request
        body = f"""fields name, url, start_date, logo.image_id, developed.name, published.name, description;
limit {limit};
offset {offset};"""

        async with client.get(
                url=BASE_URL + "companies",
                data=body,
                headers=HEADERS
        ) as resp:
            return await resp.json()

    async def create_company_page(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """Create good formatted Game Company page."""
        page = ""

        # Generate URL of company logo
        url = f"{IMAGE_BASE_URL}t_logo_med/{data['logo']['image_id'] if 'logo' in data.keys() else ''}.png"

        # Add name and description of company, attach URL to title
        page += f"[{data['name']}]({data['url']})\n"
        page += data['description'] + "\n\n" if 'description' in data.keys() else '\n'

        # Add other information
        if 'start_date' in data.keys():
            founded = datetime.utcfromtimestamp(data['start_date']).date()
        else:
            founded = "?"
        page += f"**Founded:** {founded}\n"

        page += "**Developed:** "
        page += f"{', '.join(game['name'] for game in data['developed']) if 'developed' in data.keys() else '?'}\n"

        page += "**Published:** "
        page += f"{', '.join(game['name'] for game in data['published']) if 'published' in data.keys() else '?'}"

        return page, url


def setup(bot: Bot) -> None:
    """Add/Load Games cog."""
    bot.add_cog(Games(bot))

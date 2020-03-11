import logging
import random
from datetime import datetime
from typing import Any, Dict, Optional, Union
from urllib.parse import urlencode

from discord import Embed
from discord.ext import tasks
from discord.ext.commands import BadArgument, Cog, Context, Converter, group

from bot.bot import SeasonalBot
from bot.constants import Tokens

logger = logging.getLogger(__name__)

NASA_BASE_URL = "https://api.nasa.gov"
NASA_IMAGES_BASE_URL = "https://images-api.nasa.gov"
NASA_EPIC_BASE_URL = "https://epic.gsfc.nasa.gov"

APOD_DEFAULT_PARAMS = {
    "api_key": Tokens.nasa
}


class DateConverter(Converter):
    """Parse SOL or earth date (in format YYYY-MM-DD) into `int` or `datetime`. When invalid input, raise error."""

    async def convert(self, ctx: Context, argument: str) -> Union[int, datetime]:
        """Parse date (SOL or earth) into `datetime` or `int`. When invalid value, raise error."""
        if argument.isdigit():
            return int(argument)
        try:
            date = datetime.strptime(argument, "%Y-%m-%d")
        except ValueError:
            raise BadArgument(f"Can't convert `{argument}` to `datetime` in format `YYYY-MM-DD` or `int` in SOL.")
        return date


class Space(Cog):
    """Space Cog contains commands, that show images, facts or other information about space."""

    def __init__(self, bot: SeasonalBot):
        self.bot = bot
        self.http_session = bot.http_session

        self.rovers = {}
        self.get_rovers.start()

    @tasks.loop(hours=24)
    async def get_rovers(self) -> None:
        """Get listing of rovers from NASA API and info about their start and end dates."""
        data = await self.fetch_from_nasa("mars-photos/api/v1/rovers", params={"api_key": Tokens.nasa})

        for rover in data["rovers"]:
            self.rovers[rover["name"].lower()] = {
                "min_date": rover["landing_date"],
                "max_date": rover["max_date"]
            }

    @group(name="space", invoke_without_command=True)
    async def space(self, ctx: Context) -> None:
        """Head command that contains commands about space."""
        await ctx.send_help("space")

    @space.command(name="apod")
    async def apod(self, ctx: Context, date: Optional[str] = None) -> None:
        """
        Get Astronomy Picture of Day from NASA API. Date is optional parameter, what formatting is YYYY-MM-DD.

        If date is not specified, this will get today APOD.
        """
        # Make copy of parameters
        params = APOD_DEFAULT_PARAMS.copy()
        # Parse date to params, when provided. Show error message when invalid formatting
        if date:
            try:
                params["date"] = datetime.strptime(date, "%Y-%m-%d").date().isoformat()
            except ValueError:
                await ctx.send(f"Invalid date {date}. Please make sure your date is in format YYYY-MM-DD.")
                return

        # Do request to NASA API
        result = await self.fetch_from_nasa("planetary/apod", params)

        # Create embed from result
        embed = Embed(title=f"Astronomy Picture of the Day - {result['date']}", description=result["explanation"])
        embed.set_image(url=result["url"])
        embed.set_footer(text="Powered by NASA API")

        await ctx.send(embed=embed)

    @space.command(name="nasa")
    async def nasa(self, ctx: Context, *, search_term: Optional[str] = None) -> None:
        """Get random NASA information/facts + image. Support `search_term` parameter for more specific search."""
        # Create params for request, create URL and do request
        params = {
            "media_type": "image"
        }
        if search_term:
            params["q"] = search_term

        async with self.http_session.get(url=f"{NASA_IMAGES_BASE_URL}/search?{urlencode(params)}") as resp:
            data = await resp.json()

        # Check is there any items returned
        if len(data["collection"]["items"]) == 0:
            await ctx.send(f"Can't find any items with search term `{search_term}`.")
            return

        # Get (random) item from result, that will be shown
        item = random.choice(data["collection"]["items"])

        # Create embed and send it
        embed = Embed(title=item["data"][0]["title"], description=item["data"][0]["description"])
        embed.set_image(url=item["links"][0]["href"])
        embed.set_footer(text="Powered by NASA API")

        await ctx.send(embed=embed)

    @space.command(name="epic")
    async def epic(self, ctx: Context, date: Optional[str] = None) -> None:
        """Get one of latest random image of earth from NASA EPIC API. Support date parameter, format is YYYY-MM-DD."""
        # Parse date if provided
        if date:
            try:
                show_date = datetime.strptime(date, "%Y-%m-%d").date().isoformat()
            except ValueError:
                await ctx.send(f"Invalid date {date}. Please make sure your date is in format YYYY-MM-DD.")
                return
        else:
            show_date = None

        # Generate URL and make request to API
        async with self.http_session.get(
                url=f"{NASA_EPIC_BASE_URL}/api/natural{f'/date/{show_date}' if show_date else ''}"
        ) as resp:
            data = await resp.json()

        if len(data) < 1:
            await ctx.send("Can't find any images in this date.")
            return

        # Get random item from result that will be shown
        item = random.choice(data)

        # Split date for image URL
        year, month, day = item["date"].split(" ")[0].split("-")

        image_url = f"{NASA_EPIC_BASE_URL}/archive/natural/{year}/{month}/{day}/jpg/{item['image']}.jpg"

        # Create embed, fill and send it
        embed = Embed(title="Earth Image", description=item["caption"])
        embed.set_image(url=image_url)
        embed.set_footer(text=f"Identifier: {item['identifier']} \u2022 Powered by NASA API")

        await ctx.send(embed=embed)

    @space.group(name="mars", invoke_without_command=True)
    async def mars(self,
                   ctx: Context,
                   date: DateConverter,
                   rover: Optional[str] = "curiosity"
                   ) -> None:
        """
        Get random Mars image by date. Support both SOL (martian solar day) and earth date and rovers.

        Earth date formatting is YYYY-MM-DD. Use `.space mars dates` to get all currently available rovers.
        """
        # Check does user provided correct rover
        rover = rover.lower()
        if rover not in self.rovers:
            await ctx.send(
                (
                    f"Invalid rover `{rover}`.\n"
                    f"**Rovers:** `{'`, `'.join(f'{r.capitalize()}' for r in self.rovers)}`"
                )
            )
            return

        # Create API request parameters, try to parse date
        params = {
            "api_key": Tokens.nasa
        }
        if isinstance(date, int):
            params["sol"] = date
        else:
            params["earth_date"] = date.date().isoformat()

        result = await self.fetch_from_nasa(f"mars-photos/api/v1/rovers/{rover}/photos", params)

        # Check for empty result
        if len(result["photos"]) < 1:
            err_msg = (
                f"We can't find result in date "
                f"{date.date().isoformat() if isinstance(date, datetime) else f'{date} SOL'}.\n"
                f"**Note:** Dates must match with rover's working dates. Please use `{ctx.prefix}space mars dates` to "
                "see working dates for each rover."
            )
            await ctx.send(err_msg)
            return

        # Get random item from result, generate embed with it and send
        item = random.choice(result["photos"])

        embed = Embed(title=f"{item['rover']['name']}'s {item['camera']['full_name']} Mars Image")
        embed.set_image(url=item["img_src"])
        embed.set_footer(text="Powered by NASA API")

        await ctx.send(embed=embed)

    @mars.command(name="dates", aliases=["d", "date", "rover", "rovers", "r"])
    async def dates(self, ctx: Context) -> None:
        """Get current available rovers photo date ranges."""
        await ctx.send("\n".join(
            f"**{r.capitalize()}:** {i['min_date']} **-** {i['max_date']}" for r, i in self.rovers.items()
        ))

    async def fetch_from_nasa(self, endpoint: str, params: Dict[str, Any], base: Optional[str] = NASA_BASE_URL
                              ) -> Dict[str, Any]:
        """Fetch information from NASA API, return result."""
        # Generate request URL from base URL, endpoint and parsed params
        async with self.http_session.get(url=f"{base}/{endpoint}?{urlencode(params)}") as resp:
            return await resp.json()


def setup(bot: SeasonalBot) -> None:
    """Load Space Cog."""
    # Check does bot have NASA API key in .env, when not, don't load Cog and print warning
    if not Tokens.nasa:
        logger.warning("Can't find NASA API key. Not loading Space Cog.")
        return

    bot.add_cog(Space(bot))

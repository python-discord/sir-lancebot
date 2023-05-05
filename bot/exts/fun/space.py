import logging
import random
from datetime import date, datetime
from typing import Any, Optional
from urllib.parse import urlencode

from discord import Embed
from discord.ext import tasks
from discord.ext.commands import Cog, Context, group

from bot.bot import Bot
from bot.constants import Tokens
from bot.utils.converters import DateConverter

logger = logging.getLogger(__name__)

NASA_BASE_URL = "https://api.nasa.gov"
NASA_IMAGES_BASE_URL = "https://images-api.nasa.gov"
NASA_EPIC_BASE_URL = "https://epic.gsfc.nasa.gov"

APOD_MIN_DATE = date(1995, 6, 16)


class Space(Cog):
    """Space Cog contains commands, that show images, facts or other information about space."""

    def __init__(self, bot: Bot):
        self.http_session = bot.http_session
        self.bot = bot

        self.rovers = {}
        self.get_rovers.start()

    def cog_unload(self) -> None:
        """Cancel `get_rovers` task when Cog will unload."""
        self.get_rovers.cancel()

    @tasks.loop(hours=24)
    async def get_rovers(self) -> None:
        """Get listing of rovers from NASA API and info about their start and end dates."""
        data = await self.fetch_from_nasa("mars-photos/api/v1/rovers")

        for rover in data["rovers"]:
            self.rovers[rover["name"].lower()] = {
                "min_date": rover["landing_date"],
                "max_date": rover["max_date"],
                "max_sol": rover["max_sol"]
            }

    @group(name="space", invoke_without_command=True)
    async def space(self, ctx: Context) -> None:
        """Head command that contains commands about space."""
        await self.bot.invoke_help_command(ctx)

    @space.command(name="apod")
    async def apod(self, ctx: Context, date: Optional[str]) -> None:
        """
        Get Astronomy Picture of Day from NASA API. Date is optional parameter, what formatting is YYYY-MM-DD.

        If date is not specified, this will get today APOD.
        """
        params = {}
        # Parse date to params, when provided. Show error message when invalid formatting
        if date:
            try:
                apod_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                await ctx.send(f"Invalid date {date}. Please make sure your date is in format YYYY-MM-DD.")
                return

            now = datetime.now().date()
            if APOD_MIN_DATE > apod_date or now < apod_date:
                await ctx.send(f"Date must be between {APOD_MIN_DATE.isoformat()} and {now.isoformat()} (today).")
                return

            params["date"] = apod_date.isoformat()

        result = await self.fetch_from_nasa("planetary/apod", params)

        await ctx.send(
            embed=self.create_nasa_embed(
                f"Astronomy Picture of the Day - {result['date']}",
                result["explanation"],
                result["url"]
            )
        )

    @space.command(name="nasa")
    async def nasa(self, ctx: Context, *, search_term: Optional[str]) -> None:
        """Get random NASA information/facts + image. Support `search_term` parameter for more specific search."""
        params = {
            "media_type": "image"
        }
        if search_term:
            params["q"] = search_term

        # Don't use API key, no need for this.
        data = await self.fetch_from_nasa("search", params, NASA_IMAGES_BASE_URL, use_api_key=False)
        if len(data["collection"]["items"]) == 0:
            await ctx.send(f"Can't find any items with search term `{search_term}`.")
            return

        item = random.choice(data["collection"]["items"])

        await ctx.send(
            embed=self.create_nasa_embed(
                item["data"][0]["title"],
                item["data"][0]["description"],
                item["links"][0]["href"]
            )
        )

    @space.command(name="epic")
    async def epic(self, ctx: Context, date: Optional[str]) -> None:
        """Get a random image of the Earth from the NASA EPIC API. Support date parameter, format is YYYY-MM-DD."""
        if date:
            try:
                show_date = datetime.strptime(date, "%Y-%m-%d").date().isoformat()
            except ValueError:
                await ctx.send(f"Invalid date {date}. Please make sure your date is in format YYYY-MM-DD.")
                return
        else:
            show_date = None

        # Don't use API key, no need for this.
        data = await self.fetch_from_nasa(
            f"api/natural{f'/date/{show_date}' if show_date else ''}",
            base=NASA_EPIC_BASE_URL,
            use_api_key=False
        )
        if len(data) < 1:
            await ctx.send("Can't find any images in this date.")
            return

        item = random.choice(data)

        year, month, day = item["date"].split(" ")[0].split("-")
        image_url = f"{NASA_EPIC_BASE_URL}/archive/natural/{year}/{month}/{day}/jpg/{item['image']}.jpg"

        await ctx.send(
            embed=self.create_nasa_embed(
                "Earth Image", item["caption"], image_url, f" \u2022 Identifier: {item['identifier']}"
            )
        )

    @space.group(name="mars", invoke_without_command=True)
    async def mars(
        self,
        ctx: Context,
        date: Optional[DateConverter],
        rover: str = "curiosity"
    ) -> None:
        """
        Get random Mars image by date. Support both SOL (martian solar day) and earth date and rovers.

        Earth date formatting is YYYY-MM-DD. Use `.space mars dates` to get all currently available rovers.
        """
        rover = rover.lower()
        if rover not in self.rovers:
            await ctx.send(
                (
                    f"Invalid rover `{rover}`.\n"
                    f"**Rovers:** `{'`, `'.join(f'{r.capitalize()}' for r in self.rovers)}`"
                )
            )
            return

        # When date not provided, get random SOL date between 0 and rover's max.
        if date is None:
            date = random.randint(0, self.rovers[rover]["max_sol"])

        params = {}
        if isinstance(date, int):
            params["sol"] = date
        else:
            params["earth_date"] = date.date().isoformat()

        result = await self.fetch_from_nasa(f"mars-photos/api/v1/rovers/{rover}/photos", params)
        if len(result["photos"]) < 1:
            err_msg = (
                f"We can't find result in date "
                f"{date.date().isoformat() if isinstance(date, datetime) else f'{date} SOL'}.\n"
                f"**Note:** Dates must match with rover's working dates. Please use `{ctx.prefix}space mars dates` to "
                "see working dates for each rover."
            )
            await ctx.send(err_msg)
            return

        item = random.choice(result["photos"])
        await ctx.send(
            embed=self.create_nasa_embed(
                f"{item['rover']['name']}'s {item['camera']['full_name']} Mars Image", "", item["img_src"],
            )
        )

    @mars.command(name="dates", aliases=("d", "date", "rover", "rovers", "r"))
    async def dates(self, ctx: Context) -> None:
        """Get current available rovers photo date ranges."""
        await ctx.send("\n".join(
            f"**{r.capitalize()}:** {i['min_date']} **-** {i['max_date']}" for r, i in self.rovers.items()
        ))

    async def fetch_from_nasa(
        self,
        endpoint: str,
        additional_params: Optional[dict[str, Any]] = None,
        base: Optional[str] = NASA_BASE_URL,
        use_api_key: bool = True
    ) -> dict[str, Any]:
        """Fetch information from NASA API, return result."""
        params = {}
        if use_api_key:
            params["api_key"] = Tokens.nasa.get_secret_value()

        # Add additional parameters to request parameters only when they provided by user
        if additional_params is not None:
            params.update(additional_params)

        async with self.http_session.get(url=f"{base}/{endpoint}?{urlencode(params)}") as resp:
            return await resp.json()

    def create_nasa_embed(self, title: str, description: str, image: str, footer: Optional[str] = "") -> Embed:
        """Generate NASA commands embeds. Required: title, description and image URL, footer (addition) is optional."""
        return Embed(
            title=title,
            description=description
        ).set_image(url=image).set_footer(text="Powered by NASA API" + footer)


async def setup(bot: Bot) -> None:
    """Load the Space cog."""
    if not Tokens.nasa:
        logger.warning("Can't find NASA API key. Not loading Space Cog.")
        return

    await bot.add_cog(Space(bot))

import json
import random
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from urllib.parse import urlencode

import aiohttp
from discord import Embed
from discord.ext import tasks
from discord.ext.commands import Cog, Context, group
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import Tokens
from bot.utils.converters import DateConverter

logger = get_logger(__name__)

NASA_BASE_URL = "https://api.nasa.gov"
NASA_IMAGES_BASE_URL = "https://images-api.nasa.gov"
NASA_EPIC_BASE_URL = "https://epic.gsfc.nasa.gov"

APOD_MIN_DATE = date(1995, 6, 16)


@dataclass
class NasaResult:
    """Structured result object returned by NASA API requests."""
    ok: bool
    status: int | None
    data: Any | None
    error: str | None = None


class Space(Cog):
    """Space Cog contains commands that show images, facts or other information about space."""

    def __init__(self, bot: Bot):
        self.http_session = bot.http_session
        self.bot = bot

        # Rover metadata is kept for compatibility, but Mars endpoints are archived.
        self.rovers: dict[str, dict[str, Any]] = {}
        self.get_rovers.start()

    def cog_unload(self) -> None:
        """Cancel `get_rovers` task when Cog unloads."""
        self.get_rovers.cancel()

    # ===========================
    # NASA HTTP CLIENT / HELPERS
    # ===========================

    async def fetch_from_nasa(
        self,
        endpoint: str,
        additional_params: dict[str, Any] | None = None,
        base: str | None = NASA_BASE_URL,
        use_api_key: bool = True,
        timeout: float = 10.0,
    ) -> NasaResult:
        """
        Fetch information from a NASA-related API and return a structured result.

        This wrapper:
        - Adds the NASA API key when requested.
        - Handles non-200 responses.
        - Handles non-JSON responses.
        - Catches network and timeout errors.
        """
        params: dict[str, Any] = {}

        if use_api_key:
            try:
                api_key = Tokens.nasa.get_secret_value()
            except Exception as e:
                logger.warning("NASA API key is not configured correctly: %s", e)
                return NasaResult(ok=False, status=None, data=None, error="NASA API key is not configured.")
            if not api_key:
                return NasaResult(ok=False, status=None, data=None, error="NASA API key is missing.")
            params["api_key"] = api_key

        if additional_params is not None:
            params.update(additional_params)

        if base is None:
            base = NASA_BASE_URL

        url = f"{base.rstrip('/')}/{endpoint.lstrip('/')}?{urlencode(params)}"
        logger.debug("Requesting NASA endpoint: %s", url)

        try:
            async with self.http_session.get(url, timeout=timeout) as resp:
                status = resp.status
                content_type = resp.headers.get("Content-Type", "")

                # Try JSON first when content type suggests it.
                if "application/json" in content_type or "json" in content_type:
                    try:
                        data = await resp.json()
                    except (aiohttp.ContentTypeError, json.JSONDecodeError) as e:
                        logger.warning("Failed to decode JSON from NASA response (%s): %s", url, e)
                        text = await resp.text()
                        return NasaResult(
                            ok=False,
                            status=status,
                            data=None,
                            error=f"NASA returned invalid JSON (status {status}).",
                        )
                else:
                    # Non-JSON response; read as text for logging and user-friendly error.
                    text = await resp.text()
                    logger.warning(
                        "NASA returned non-JSON response (status %s, content-type %s) for %s: %s",
                        status,
                        content_type,
                        url,
                        text[:500],
                    )
                    return NasaResult(
                        ok=False,
                        status=status,
                        data=None,
                        error=f"NASA returned an unexpected response (status {status}).",
                    )

                if 200 <= status < 300:
                    return NasaResult(ok=True, status=status, data=data)
                else:
                    logger.warning("NASA API returned non-success status %s for %s", status, url)
                    return NasaResult(
                        ok=False,
                        status=status,
                        data=data,
                        error=f"NASA API returned status {status}.",
                    )

        except TimeoutError:
            logger.warning("NASA API request timed out for %s", url)
            return NasaResult(ok=False, status=None, data=None, error="NASA API request timed out.")
        except aiohttp.ClientError as e:
            logger.warning("NASA API request failed for %s: %s", url, e)
            return NasaResult(ok=False, status=None, data=None, error="NASA API request failed.")
        except Exception as e:
            logger.exception("Unexpected error while requesting NASA API for %s: %s", url, e)
            return NasaResult(ok=False, status=None, data=None, error="Unexpected error while contacting NASA API.")

    def create_nasa_embed(self, title: str, description: str, image: str, footer: str | None = "") -> Embed:
        """Generate NASA command embeds. Required: title, description, and image URL; footer is optional."""
        return (
            Embed(
                title=title,
                description=description,
            )
            .set_image(url=image)
            .set_footer(text="Powered by NASA API" + (footer or ""))
        )

    # ===========================
    # BACKGROUND TASKS
    # ===========================

    @tasks.loop(hours=24)
    async def get_rovers(self) -> None:
        """
        Get listing of rovers from NASA API and info about their start and end dates.

        NOTE: The Mars Rover Photos API has been archived by NASA.
        This task is kept for compatibility but will not populate rover data reliably.
        """
        logger.info("Refreshing Mars rover metadata from NASA (archived API).")
        result = await self.fetch_from_nasa("mars-photos/api/v1/rovers")

        if not result.ok:
            logger.warning(
                "Failed to refresh rover metadata from NASA (archived API). Status: %s, Error: %s",
                result.status,
                result.error,
            )
            self.rovers.clear()
            return

        data = result.data
        if not isinstance(data, dict) or "rovers" not in data:
            logger.warning("Unexpected rover metadata format from NASA: %r", data)
            self.rovers.clear()
            return

        self.rovers.clear()
        for rover in data.get("rovers", []):
            try:
                name = rover["name"].lower()
                self.rovers[name] = {
                    "min_date": rover.get("landing_date"),
                    "max_date": rover.get("max_date"),
                    "max_sol": rover.get("max_sol"),
                }
            except KeyError:
                logger.warning("Skipping malformed rover entry: %r", rover)

        logger.info("Loaded rover metadata for rovers: %s", ", ".join(self.rovers.keys()) or "none")

    # ===========================
    # COMMAND GROUP
    # ===========================

    @group(name="space", invoke_without_command=True)
    async def space(self, ctx: Context) -> None:
        """Head command that contains commands about space."""
        await self.bot.invoke_help_command(ctx)

    # ===========================
    # APOD COMMAND
    # ===========================

    @space.command(name="apod")
    async def apod(self, ctx: Context, date: str | None) -> None:
        """
        Get Astronomy Picture of the Day from NASA API. Date is optional, format is YYYY-MM-DD.

        If date is not specified, this will get today's APOD.
        """
        params: dict[str, Any] = {}

        if date:
            try:
                apod_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=UTC).date()
            except ValueError:
                await ctx.send(f"Invalid date {date}. Please make sure your date is in format YYYY-MM-DD.")
                return

            now = datetime.now(tz=UTC).date()
            if apod_date < APOD_MIN_DATE or now < apod_date:
                await ctx.send(
                    f"Date must be between {APOD_MIN_DATE.isoformat()} and {now.isoformat()} (today)."
                )
                return

            params["date"] = apod_date.isoformat()

        result = await self.fetch_from_nasa("planetary/apod", params)

        if not result.ok or not isinstance(result.data, dict):
            msg = result.error or "Failed to fetch Astronomy Picture of the Day from NASA."
            await ctx.send(msg)
            return

        data = result.data
        missing = [k for k in ("date", "explanation", "url") if k not in data]
        if missing:
            logger.warning("APOD response missing keys %s: %r", missing, data)
            await ctx.send("NASA returned an unexpected response for APOD.")
            return

        await ctx.send(
            embed=self.create_nasa_embed(
                f"Astronomy Picture of the Day - {data['date']}",
                data["explanation"],
                data["url"],
            )
        )

    # ===========================
    # NASA IMAGES SEARCH COMMAND
    # ===========================

    @space.command(name="nasa")
    async def nasa(self, ctx: Context, *, search_term: str | None) -> None:
        """Get random NASA information/facts + image. Supports `search_term` for more specific search."""
        params: dict[str, Any] = {"media_type": "image"}
        if search_term:
            params["q"] = search_term

        result = await self.fetch_from_nasa(
            "search",
            additional_params=params,
            base=NASA_IMAGES_BASE_URL,
            use_api_key=False,
        )

        if not result.ok:
            msg = result.error or "Failed to fetch images from NASA."
            await ctx.send(msg)
            return

        data = result.data
        try:
            items = data["collection"]["items"]
        except (TypeError, KeyError):
            logger.warning("Unexpected NASA images response format: %r", data)
            await ctx.send("NASA returned an unexpected response for image search.")
            return

        if not items:
            await ctx.send(f"Can't find any items with search term `{search_term}`.")
            return

        item = random.choice(items)
        try:
            title = item["data"][0]["title"]
            description = item["data"][0].get("description", "No description provided.")
            image_url = item["links"][0]["href"]
        except (KeyError, IndexError, TypeError):
            logger.warning("Malformed NASA image item: %r", item)
            await ctx.send("NASA returned an unexpected image result.")
            return

        await ctx.send(
            embed=self.create_nasa_embed(
                title,
                description,
                image_url,
            )
        )

    # ===========================
    # EPIC COMMAND
    # ===========================

    @space.command(name="epic")
    async def epic(self, ctx: Context, date: str | None) -> None:
        """Get a random image of the Earth from the NASA EPIC API. Date format is YYYY-MM-DD."""
        if date:
            try:
                show_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=UTC).date().isoformat()
            except ValueError:
                await ctx.send(f"Invalid date {date}. Please make sure your date is in format YYYY-MM-DD.")
                return
        else:
            show_date = None

        endpoint = f"api/natural{f'/date/{show_date}' if show_date else ''}"

        result = await self.fetch_from_nasa(
            endpoint,
            base=NASA_EPIC_BASE_URL,
            use_api_key=False,
        )

        if not result.ok:
            msg = result.error or "Failed to fetch EPIC images from NASA."
            await ctx.send(msg)
            return

        data = result.data
        if not isinstance(data, list) or len(data) < 1:
            await ctx.send("Can't find any images for this date.")
            return

        item = random.choice(data)
        try:
            date_str = item["date"].split(" ")[0]
            year, month, day = date_str.split("-")
            image_id = item["image"]
            caption = item.get("caption", "No caption provided.")
            identifier = item.get("identifier", "Unknown")
        except (KeyError, ValueError, AttributeError):
            logger.warning("Malformed EPIC item: %r", item)
            await ctx.send("NASA returned an unexpected EPIC image result.")
            return

        image_url = f"{NASA_EPIC_BASE_URL}/archive/natural/{year}/{month}/{day}/jpg/{image_id}.jpg"

        await ctx.send(
            embed=self.create_nasa_embed(
                "Earth Image",
                caption,
                image_url,
                f" \u2022 Identifier: {identifier}",
            )
        )

    # ===========================
    # MARS COMMANDS (ARCHIVED API)
    # ===========================

    @space.group(name="mars", invoke_without_command=True)
    async def mars(
        self,
        ctx: Context,
        date: DateConverter | None,
        rover: str = "curiosity",
    ) -> None:
        """
        Get random Mars image by date. Supports both SOL (martian solar day) and Earth date and rovers.

        NOTE: The Mars Rover Photos API used by this command has been archived by NASA and is no longer
        reliable. This command is kept for compatibility but will currently respond with a notice.
        """
        await ctx.send(
            "The NASA Mars Rover Photos API used by this command has been archived by NASA and is no longer "
            "reliably available. As a result, `.space mars` is temporarily disabled."
        )

    @mars.command(name="dates", aliases=("d", "date", "rover", "rovers", "r"))
    async def dates(self, ctx: Context) -> None:
        """Get current available rover photo date ranges (informational only; API is archived)."""
        if not self.rovers:
            await ctx.send(
                "Rover metadata could not be loaded because the Mars Rover Photos API has been archived by NASA."
            )
            return

        await ctx.send(
            "\n".join(
                f"**{r.capitalize()}:** {i['min_date']} **-** {i['max_date']}"
                for r, i in self.rovers.items()
            )
        )


async def setup(bot: Bot) -> None:
    """Load the Space cog."""
    if not Tokens.nasa:
        logger.warning("Can't find NASA API key. Space Cog will not be loaded.")
        return

    await bot.add_cog(Space(bot))
    return

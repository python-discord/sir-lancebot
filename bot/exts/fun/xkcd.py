import re
from random import randint

import discord
from discord import Embed, ui
from discord.ext import tasks
from discord.ext.commands import Cog, Context, command
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import Colours

log = get_logger(__name__)

COMIC_FORMAT = re.compile(r"latest|[0-9]+")
BASE_URL = "https://xkcd.com"


class XKCD(Cog):
    """Retrieving XKCD comics."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.latest_comic_info: dict[str, str | int] = {}
        self.get_latest_comic_info.start()

    def cog_unload(self) -> None:
        """Cancels refreshing of the task for refreshing the most recent comic info."""
        self.get_latest_comic_info.cancel()

    @tasks.loop(minutes=30)
    async def get_latest_comic_info(self) -> None:
        """Refreshes latest comic's information ever 30 minutes. Also used for finding a random comic."""
        async with self.bot.http_session.get(f"{BASE_URL}/info.0.json") as resp:
            if resp.status == 200:
                self.latest_comic_info = await resp.json()
            else:
                log.debug(f"Failed to get latest XKCD comic information. Status code {resp.status}")

    @command(name="xkcd")
    async def fetch_xkcd_comics(self, ctx: Context, comic: str | None) -> None:
        """
        Getting an xkcd comic's information along with the image.

        To get a random comic, don't type any number as an argument. To get the latest, type 'latest'.
        """
        embed = Embed(title=f"XKCD comic '{comic}'")

        embed.colour = Colours.soft_red

        if comic and (comic := re.match(COMIC_FORMAT, comic)) is None:
            embed.description = "Comic parameter should either be an integer or 'latest'."
            await ctx.send(embed=embed)
            return

        comic = randint(1, self.latest_comic_info["num"]) if comic is None else comic.group(0)

        if comic == "latest":
            info = self.latest_comic_info
        else:
            async with self.bot.http_session.get(f"{BASE_URL}/{comic}/info.0.json") as resp:
                if resp.status == 200:
                    info = await resp.json()
                else:
                    embed.title = f"XKCD comic #{comic}"
                    embed.description = f"{resp.status}: Could not retrieve xkcd comic #{comic}."
                    log.debug(f"Retrieving xkcd comic #{comic} failed with status code {resp.status}.")
                    await ctx.send(embed=embed)
                    return

        date = f"{info['year']}/{info['month']}/{info['day']}"
        view = self._build_comic_view(info["num"], info["safe_title"], info["img"], info["alt"], date)

        await ctx.send(view=view)

    @staticmethod
    def _build_comic_view(num: int, title: str, image_url: str, alt_text: str, date: str) -> ui.LayoutView:
        """Build a layout view to display the comic, if possible."""
        view = ui.LayoutView(timeout=0)

        url = f"{BASE_URL}/{num}"
        if image_url[-3:] in ("jpg", "png", "gif"):
            image_display = ui.MediaGallery(discord.MediaGalleryItem(media=image_url))
        else:
            image_display = ui.TextDisplay(
                "The selected comic is interactive, and cannot be displayed within a discord message.\n"
                f"Comic can be viewed [here]({url})."
            )

        container = ui.Container(
            ui.TextDisplay(f"### [XKCD comic #{num} — {title}]({url})"),
            image_display,
        )
        if alt_text:
            container.add_item(ui.TextDisplay(alt_text))
        container.add_item(ui.TextDisplay(f"-# {date}"))
        view.add_item(container)

        return view


async def setup(bot: Bot) -> None:
    """Load the XKCD cog."""
    await bot.add_cog(XKCD(bot))

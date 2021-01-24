import logging
from random import randint
from typing import Dict, Optional, Union

from discord import Embed
from discord.ext import tasks
from discord.ext.commands import Cog, Context, command

from bot.bot import Bot
from bot.constants import Colours

log = logging.getLogger(__name__)

URL = "https://xkcd.com/{0}/info.0.json"
LATEST = "https://xkcd.com/info.0.json"


class XKCD(Cog):
    """Retrieving XKCD comics."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.latest_comic_info: Dict[str, Union[str, int]] = {}
        self.get_latest_comic_info.start()

    def cog_unload(self) -> None:
        """Cancels refreshing of the task for refreshing the most recent comic info."""
        self.get_latest_comic_info.cancel()

    @tasks.loop(minutes=30)
    async def get_latest_comic_info(self) -> None:
        """Refreshes latest comic's information ever 30 minutes. Also used for finding a random comic."""
        async with self.bot.http_session.get(LATEST) as resp:
            if resp.status == 200:
                self.latest_comic_info = await resp.json()
            else:
                log.debug(f"Failed to get latest XKCD comic information. Status code {resp.status}")

    @command(name="xkcd")
    async def fetch_xkcd_comics(self, ctx: Context, comic: Optional[str]) -> None:
        """
        Getting an xkcd comic's information along with the image.

        To get a random comic, don't type any number as an argument. To get the latest, enter 0.
        """
        embed = Embed()

        comic = comic or randint(1, self.latest_comic_info['num'])

        if comic == "latest":
            info = self.latest_comic_info

        else:
            async with self.bot.http_session.get(URL.format(comic)) as resp:
                if resp.status == 200:
                    info = await resp.json()
                else:
                    embed.description = f"{resp.status}: Could not retrieve xkcd comic #{comic}."
                    embed.colour = Colours.soft_red
                    log.debug(f"Retrieving xkcd comic #{comic} failed with status code {resp.status}.")
                    await ctx.send(embed=embed)
                    return

        embed.set_image(url=info["img"])
        date = f"{info['year']}/{info['month']}/{info['day']}"
        embed.set_footer(text=f"{date} - #{info['num']}, \'{info['safe_title']}\'")

        await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Loading the XKCD cog."""
    bot.add_cog(XKCD(bot))

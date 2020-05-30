import logging
import random

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class XKCD(commands.Cog):
    """A cog for posting the XKCD ."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="xkcd")
    async def fetch_xkcd_comics(self, ctx: commands.Context, comic: str = "latest") -> None:
        """Read your Fav XKCD comics."""
        if comic not in ["random", "latest"]:
            url = f"https://xkcd.com/{comic}/info.0.json"
        else:
            url = "https://xkcd.com/info.0.json"

        # ---- random choice -----
        if comic == "random":
            async with self.bot.http_session.get(url) as r:
                json_data = await r.json()
            random_pick = random.randint(1, int(json_data["num"]))
            url = f"https://xkcd.com/{random_pick}/info.0.json"

        log.trace(f"Querying xkcd API: {url}")
        async with self.bot.http_session.get(url) as r:
            if r.status == "200":
                json_data = await r.json()
            else:
                # ----- Exception handling | Guides to use ------
                log.warning(f"Received response {r.status} from: {url}")
                # -- get the latest comic number ---
                url = f"https://xkcd.com/info.0.json"
                async with self.bot.http_session.get(url) as r:
                    latest_data = await r.json()

                # --- beautify response ---
                latest_num = latest_data["num"]
                resp = discord.Embed(
                    title="Guides | Usage",
                    description=f'''
                    .xkcd latest (Retrieves the latest comic)
                    .xkcd random (Retrieves random comic)
                    .xkcd number (Enter a comic number between 1 & {latest_num})
                    '''
                )
                return await ctx.send(embed=resp)

        # --- response variables ----
        day, month, year = json_data["day"], json_data["month"], json_data["year"]
        comic_number = json_data["num"]

        # ---- beautify response ----
        embed = discord.Embed(
            title=json_data['title'],
            description=json_data["alt"]
        )
        embed.set_image(url=json_data['img'])
        embed.set_footer(text=f"Post date : {day}-{month}-{year} | xkcd comics - {comic_number}")

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """XKCD Cog load."""
    bot.add_cog(XKCD(bot))

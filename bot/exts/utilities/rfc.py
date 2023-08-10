import datetime
import logging

from discord import Embed
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

logger = logging.getLogger(__name__)

BASE_URL = "https://datatracker.ietf.org/doc/rfc{query}/doc.json"


class Rfc(commands.Cog):
    """Retrieve RFCs from their ID."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def rfc(self, ctx: commands.Context, query: int) -> None:
        """Sends the corresponding RFC with the given ID."""
        async with self.bot.http_session.get(BASE_URL.format(query=query)) as resp:
            if resp.status != 200:
                error = Embed(
                    title="RFC not found",
                    description=f"RFC {query} was not found.",
                    colour=Colours.soft_red,
                )

                await ctx.send(embed=error)
                return

            data = await resp.json()

            description = (
                data["abstract"]
                or f"[Link](https://datatracker.ietf.org/doc/rfc{query})"
            )
            title = data["title"]

            embed = Embed(
                title=f"RFC {query} - {title}",
                description=description,
                colour=Colours.gold,
            )

            embed.add_field(
                name="Current Revision",
                value=data["rev"] or len(data["rev_history"]),
            )

            created = data["rev_history"][0]["published"]
            created = datetime.datetime.strptime(created, "%Y-%m-%dT%H:%M:%S%z")

            embed.add_field(name="Created", value=created.strftime("%Y-%m-%d"))

            await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the Rfc cog."""
    await bot.add_cog(Rfc(bot))

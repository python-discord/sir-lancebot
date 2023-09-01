import datetime
import logging

import pydantic
from discord import Embed
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, Roles
from bot.utils.decorators import whitelist_override

logger = logging.getLogger(__name__)

API_URL = "https://datatracker.ietf.org/doc/rfc{rfc_id}/doc.json"
DOCUMENT_URL = "https://datatracker.ietf.org/doc/rfc{rfc_id}"


class RfcDocument(pydantic.BaseModel):
    """Represents an RFC document."""

    title: str
    description: str
    revisions: str
    created: datetime.datetime


class Rfc(commands.Cog):
    """Retrieves RFCs by their ID."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.cache: dict[int, RfcDocument] = {}

    async def retrieve_data(self, rfc_id: int) -> RfcDocument | None:
        """Retrieves the RFC from the cache or API, and adds to the cache if it does not exist."""
        if rfc_id in self.cache:
            return self.cache[rfc_id]

        async with self.bot.http_session.get(API_URL.format(rfc_id=rfc_id)) as resp:
            if resp.status != 200:
                return None

            data = await resp.json()

        description = data["abstract"]

        revisions = data["rev"] or len(data["rev_history"])

        raw_date = data["rev_history"][0]["published"]
        creation_date = datetime.datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S%z")

        document = RfcDocument(
            title=data["title"],
            description=description,
            revisions=revisions,
            created=creation_date,
        )

        self.cache[rfc_id] = document

        return document

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command()
    @commands.guild_only()
    @whitelist_override(roles=(Roles.everyone,))
    async def rfc(self, ctx: commands.Context, rfc_id: int) -> None:
        """Sends the corresponding RFC with the given ID."""
        document = await self.retrieve_data(rfc_id)

        if not document:
            embed = Embed(
                title="RFC not found",
                description=f"RFC {rfc_id} does not exist.",
                colour=Colours.soft_red,
            )

            await ctx.send(embed=embed)

            return

        logger.info(f"Fetching RFC {rfc_id}")

        embed = Embed(
            title=f"RFC {rfc_id} - {document.title}",
            description=document.description,
            colour=Colours.gold,
            url=DOCUMENT_URL.format(rfc_id=rfc_id),
        )

        embed.add_field(
            name="Current Revision",
            value=document.revisions,
        )

        embed.add_field(
            name="Created",
            value=document.created.strftime("%Y-%m-%d"),
        )
        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the Rfc cog."""
    await bot.add_cog(Rfc(bot))

import json
from pathlib import Path
from random import choice

import discord
from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import Colours

log = get_logger(__name__)

FACTS = json.loads(Path("bot/resources/holidays/valentines/valentine_facts.json").read_text("utf8"))


class ValentineFacts(commands.Cog):
    """A Cog for displaying facts about Saint Valentine."""

    @commands.command(aliases=("whoisvalentine", "saint_valentine"))
    async def who_is_valentine(self, ctx: commands.Context) -> None:
        """Displays info about Saint Valentine."""
        embed = discord.Embed(
            title="Who is Saint Valentine?",
            description=FACTS["whois"],
            color=Colours.pink
        )
        embed.set_thumbnail(
            url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Saint_Valentine_-_"
                "facial_reconstruction.jpg/1024px-Saint_Valentine_-_facial_reconstruction.jpg"
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def valentine_fact(self, ctx: commands.Context) -> None:
        """Shows a random fact about Valentine's Day."""
        embed = discord.Embed(
            title=choice(FACTS["titles"]),
            description=choice(FACTS["text"]),
            color=Colours.pink
        )

        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the Who is Valentine Cog."""
    await bot.add_cog(ValentineFacts())

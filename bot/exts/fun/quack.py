import logging
import random
from typing import Literal, Optional

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES

API_URL = 'https://quackstack.pythondiscord.com'

log = logging.getLogger(__name__)


class Quackstack(commands.Cog):
    """Cog used for wrapping Quackstack."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def quack(
        self,
        ctx: commands.Context,
        ducktype: Literal["duck", "manduck"] = "duck",
        *,
        seed: Optional[str] = None
    ) -> None:
        """
        Use the Quackstack API to generate a random duck.

        If a seed is provided, a duck is generated based on the given seed.
        Either "duck" or "manduck" can be provided to change the duck type generated.
        """
        ducktype = ducktype.lower()
        quackstack_url = f"{API_URL}/{ducktype}"
        params = {}
        if seed is not None:
            try:
                seed = int(seed)
            except ValueError:
                # We just need to turn the string into an integer any way possible
                seed = int.from_bytes(seed.encode(), "big")
            params["seed"] = seed

        async with self.bot.http_session.get(quackstack_url, params=params) as response:
            error_embed = discord.Embed(
                title=random.choice(NEGATIVE_REPLIES),
                description="The request failed. Please try again later.",
                color=Colours.soft_red,
            )
            if response.status != 200:
                log.error(f"Response to Quackstack returned code {response.status}")
                await ctx.send(embed=error_embed)
                return

            data = await response.json()
            file = data["file"]

        embed = discord.Embed(
            title=f"Quack! Here's a {ducktype} for you.",
            description=f"A {ducktype} from Quackstack.",
            color=Colours.grass_green,
            url=f"{API_URL}/docs"
        )

        embed.set_image(url=API_URL + file)

        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Loads the Quack cog."""
    await bot.add_cog(Quackstack(bot))

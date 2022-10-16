import json
from pathlib import Path

from discord import Embed
from discord.ext import commands

from bot.bot import Bot
from bot.utils.randomization import RandomCycle

EMBED_DATA = RandomCycle(json.loads(Path("bot/resources/holidays/earth_day/save_the_planet.json").read_text("utf8")))


class SaveThePlanet(commands.Cog):
    """A cog that teaches users how they can help our planet."""

    @commands.command(aliases=("savetheearth", "saveplanet", "saveearth"))
    async def savetheplanet(self, ctx: commands.Context) -> None:
        """Responds with a random tip on how to be eco-friendly and help our planet."""
        return_embed = Embed.from_dict(next(EMBED_DATA))
        await ctx.send(embed=return_embed)


async def setup(bot: Bot) -> None:
    """Load the Save the Planet Cog."""
    await bot.add_cog(SaveThePlanet())

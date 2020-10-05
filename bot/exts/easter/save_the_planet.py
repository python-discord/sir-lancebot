import json
from pathlib import Path

from discord import Embed
from discord.ext import commands

from bot.utils import RandomCycle

EMBED_DATA = []


class SaveThePlanet(commands.Cog):
    """A cog that teaches users how they can help our planet."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        with Path("bot/resources/easter/save_the_planet.json").open('r', encoding='utf8') as f:
            global EMBED_DATA
            EMBED_DATA = RandomCycle(json.load(f))

    @commands.command(aliases=('savetheearth', 'saveplanet', 'saveearth'))
    async def savetheplanet(self, ctx: commands.Context) -> None:
        """Responds with a random tip on how to be eco-friendly and help our planet."""
        return_embed = Embed.from_dict(next(EMBED_DATA))
        await ctx.send(embed=return_embed)


def setup(bot: commands.Bot) -> None:
    """Save the Planet Cog load."""
    bot.add_cog(SaveThePlanet(bot))

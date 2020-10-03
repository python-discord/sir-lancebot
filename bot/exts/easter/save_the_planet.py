import json
import random
from pathlib import Path

from discord import Embed
from discord.ext import commands


class SaveThePlanet(commands.Cog):
    """A cog that teaches users how they can help our planet."""

    embed_data = []

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        with open(Path("bot/resources/easter/save_the_planet.json"), 'r', encoding='utf8') as f:
            for embed in json.load(f):
                self.embed_data.append(embed)

    @commands.command(aliases=('savetheearth', 'saveplanet', 'saveearth'))
    async def savetheplanet(self, ctx: commands.Context) -> None:
        """Responds with a random tip on how to be eco-friendly and help our planet."""
        return_embed = Embed.from_dict(random.choice(self.embed_data))
        await ctx.send(embed=return_embed)


def setup(bot: commands.Bot) -> None:
    """Save the Planet Cog load."""
    bot.add_cog(SaveThePlanet(bot))

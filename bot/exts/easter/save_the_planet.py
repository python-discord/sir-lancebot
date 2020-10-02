import json
import random
from pathlib import Path

from discord import Embed
from discord.ext import commands


class SaveThePlanet(commands.Cog):
    """A cog that teaches users how they can help our planet."""

    json_embeds = []

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        with open(Path("bot/resources/save_the_planet.json"), 'r', encoding='utf8') as f:
            for key, embed in json.load(f).items():
                self.json_embeds[key] = embed

    @commands.command(aliases=('savetheearth', 'saveplanet', 'saveearth'))
    async def savetheplanet(self, ctx: commands.Context) -> None:
        """Responds with a random tip on how to be ecofriendly and help our planet."""
        await ctx.send(embed=Embed.from_dict(random.choice(self.json_embeds)))


def setup(bot: commands.Bot) -> None:
    """save_the_planet Cog load."""
    bot.add_cog(SaveThePlanet(bot))

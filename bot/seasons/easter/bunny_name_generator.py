import random
import json
import logging

from discord.ext import commands
from pathlib import Path


log = logging.getLogger(__name__)

with open(Path("bot", "resources", "easter", "bunny_names.json"), "r", encoding="utf8") as f:
    BUNNY_NAMES = json.load(f)


class BunnyNameGenerator(commands.Cog):
    """Generate a random bunny name, or bunnify your Discord username!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def bunnyname(self, ctx):
        """Picks a random bunny name from a JSON file"""

        await ctx.send(random.choice(BUNNY_NAMES["names"]))

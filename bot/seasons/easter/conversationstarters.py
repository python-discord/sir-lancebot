import json
import logging
import random
from pathlib import Path

from discord.ext import commands

log = logging.getLogger(__name__)

with open(Path("bot/resources/easter/starter.json"), "r", encoding="utf8") as f:
    starters = json.load(f)


class ConvoStarters(commands.Cog):
    """Easter conversation topics."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def topic(self, ctx):
        """Responds with a random topic to start a conversation."""
        await ctx.send(random.choice(starters['starters']))


def setup(bot):
    """Conversation starters Cog load."""
    bot.add_cog(ConvoStarters(bot))
    log.info("ConvoStarters cog loaded")

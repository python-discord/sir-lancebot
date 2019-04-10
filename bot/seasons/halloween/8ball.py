import asyncio
import json
import logging
import random
from pathlib import Path

from discord.ext import commands

log = logging.getLogger(__name__)

with open(Path('bot', 'resources', 'halloween', 'responses.json'), 'r', encoding="utf8") as f:
    responses = json.load(f)


class EightBall(commands.Cog):
    """Spooky Eightball answers."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=('spooky8ball',))
    async def spookyeightball(self, ctx, question: str):
        """Responds with a random response to a question."""

        choice = random.choice(responses)
        if len(choice) == 1:
            await ctx.send(choice[0])
        else:
            for x in choice:
                await ctx.send(x)
                asyncio.sleep(random.randint(2, 5))
                await ctx.send(x)


def setup(bot):
    """Conversation starters Cog load."""

    bot.add_cog(EightBall(bot))
    log.info("8Ball cog loaded")

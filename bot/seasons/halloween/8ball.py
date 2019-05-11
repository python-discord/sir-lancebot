import asyncio
import json
import logging
import random
from pathlib import Path

from discord.ext import commands

log = logging.getLogger(__name__)

with open(Path('bot', 'resources', 'halloween', 'responses.json'), 'r', encoding="utf8") as f:
    responses = json.load(f)


class SpookyEightBall(commands.Cog):
    """Spooky Eightball answers."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=('spooky8ball',))
    async def spookyeightball(self, ctx, *, question: str):
        """Responds with a random response to a question."""
        choice = random.choice(responses['responses'])
        msg = await ctx.send(choice[0])
        if len(choice) > 1:
            await asyncio.sleep(random.randint(2, 5))
            await msg.edit(content=f"{choice[0]} \n{choice[1]}")


def setup(bot):
    """Spooky Eight Ball Cog Load."""

    bot.add_cog(SpookyEightBall(bot))
    log.info("SpookyEightBall cog loaded")

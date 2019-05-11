import asyncio
import json
import logging
import random
from pathlib import Path

import discord
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
        if len(choice) == 1:
            await ctx.send(choice[0])
        else:
            emb = discord.Embed(colour=0x00f2ff)
            emb.add_field(name=f'Question from {ctx.author.name}', value=question)
            emb.add_field(name='Answer', value=choice[0])
            msg = await ctx.send(embed=emb)
            await asyncio.sleep(random.randint(2, 5))
            emb.set_field_at(1, name='Answer', value=f'{choice[0]} \n {choice[1]}')
            await msg.edit(embed=emb)


def setup(bot):
    """Spooky Eight Ball Cog Load."""

    bot.add_cog(EightBall(bot))
    log.info("8Ball cog loaded")

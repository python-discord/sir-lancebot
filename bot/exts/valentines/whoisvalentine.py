import json
import logging
from pathlib import Path
from random import choice

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)

with open(Path("bot/resources/valentines/valentine_facts.json"), "r") as file:
    FACTS = json.load(file)


class ValentineFacts(commands.Cog):
    """A Cog for displaying facts about Saint Valentine."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=('whoisvalentine', 'saint_valentine'))
    async def who_is_valentine(self, ctx: commands.Context) -> None:
        """Displays info about Saint Valentine."""
        embed = discord.Embed(
            title="Who is Saint Valentine?",
            description=FACTS['whois'],
            color=Colours.pink
        )
        embed.set_thumbnail(
            url='https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Saint_Valentine_-_'
                'facial_reconstruction.jpg/1024px-Saint_Valentine_-_facial_reconstruction.jpg'
        )

        await ctx.channel.send(embed=embed)

    @commands.command()
    async def valentine_fact(self, ctx: commands.Context) -> None:
        """Shows a random fact about Valentine's Day."""
        embed = discord.Embed(
            title=choice(FACTS['titles']),
            description=choice(FACTS['text']),
            color=Colours.pink
        )

        await ctx.channel.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Who is Valentine Cog load."""
    bot.add_cog(ValentineFacts(bot))

import json
import logging
import os
from pathlib import Path
from random import shuffle

import discord
from discord.ext import commands

log = logging.getLogger(__name__)
DIR = "bot/resources/evergreen/game_recs"
game_recs = []


class RecommendGame(commands.Cog):
    """Commands related to recommending games."""

    def __init__(self, bot):
        self.bot = bot
        self.populate_recs()

    @commands.command(name="recommend_game")
    async def recommend_game(self, ctx):
        """Sends an Embed of a random game recommendation."""
        if not game_recs:
            self.populate_recs()
            game = game_recs.pop()
        else:
            game = game_recs.pop()

        embed = discord.Embed(
            title=game['title'],
            url=game['wikiLink'],
            color=discord.Colour.blue()
        )

        author = self.bot.get_user(int(game['author']))
        embed.set_author(name=author.name, icon_url=author.avatar_url)
        embed.set_image(url=game['image'])
        embed.add_field(name="Recommendation", value=game['recText'])

        await ctx.send(embed=embed)

    def populate_recs(self):
        """Populates the game_recs list from resources."""
        for file_url in os.listdir(DIR):
            with Path(DIR, file_url).open(encoding='utf-8') as file:
                data = json.load(file)
            game_recs.append(data)
        shuffle(game_recs)


def setup(bot):
    """Loads the RecommendGame cog."""
    bot.add_cog(RecommendGame(bot))
    log.info("Recommend_Game cog loaded")

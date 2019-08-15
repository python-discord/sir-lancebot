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
        author = self.bot.get_user(int(game['author']))

        # Creating and formatting Embed
        embed = discord.Embed(color=discord.Colour.blue())
        embed.set_author(name=author.name, icon_url=author.avatar_url)
        embed.set_image(url=game['image'])
        embed.add_field(name='Recommendation: ' + game['title'] + '\n' + game['wikiLink'], value=game['recText'])

        await ctx.send(embed=embed)

    def populate_recs(self):
        """Populates the list `game_recs` from resources."""
        for file_url in os.listdir(DIR):
            with Path(DIR, file_url).open(encoding='utf-8') as file:
                data = json.load(file)
            game_recs.append(data)
        shuffle(game_recs)


def setup(bot):
    """Loads the RecommendGame cog."""
    bot.add_cog(RecommendGame(bot))
    log.info("Recommend_Game cog loaded")

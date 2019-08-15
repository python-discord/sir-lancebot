import json
import logging
from pathlib import Path
from random import shuffle

import discord
from discord.ext import commands

log = logging.getLogger(__name__)
DIR = Path("bot/resources/evergreen/game_recs")
game_recs = []

# Populate the list `game_recs` with resource files
for file_url in DIR.glob("*.json"):
    with Path(file_url).open(encoding='utf-8') as file:
        data = json.load(file)
    game_recs.append(data)
shuffle(game_recs)


class RecommendGame(commands.Cog):
    """Commands related to recommending games."""

    def __init__(self, bot):
        self.bot = bot
        self.index = 0

    @commands.command(name="recommend_game", aliases=['gameRec', 'recommendGame'])
    async def recommend_game(self, ctx):
        """Sends an Embed of a random game recommendation."""
        if self.index < len(game_recs):
            game = game_recs[self.index]
            self.index += 1
        else:
            self.index = 0
            shuffle(game_recs)
            game = game_recs[self.index]
            self.index += 1

        author = self.bot.get_user(int(game['author']))

        # Creating and formatting Embed
        embed = discord.Embed(color=discord.Colour.blue())
        embed.set_author(name=author.name, icon_url=author.avatar_url)
        embed.set_image(url=game['image'])
        embed.add_field(name='Recommendation: ' + game['title'] + '\n' + game['wikiLink'], value=game['recText'])

        await ctx.send(embed=embed)


def setup(bot):
    """Loads the RecommendGame cog."""
    bot.add_cog(RecommendGame(bot))
    log.info("RecommendGame cog loaded")

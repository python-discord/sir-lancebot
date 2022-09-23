import json
import logging
from pathlib import Path
from random import shuffle

import discord
from discord.ext import commands

from bot.bot import Bot

log = logging.getLogger(__name__)
game_recs = []

# Populate the list `game_recs` with resource files
for rec_path in Path("bot/resources/fun/game_recs").glob("*.json"):
    data = json.loads(rec_path.read_text("utf8"))
    game_recs.append(data)
shuffle(game_recs)


class RecommendGame(commands.Cog):
    """Commands related to recommending games."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.index = 0

    @commands.command(name="recommendgame", aliases=("gamerec",))
    async def recommend_game(self, ctx: commands.Context) -> None:
        """Sends an Embed of a random game recommendation."""
        if self.index >= len(game_recs):
            self.index = 0
            shuffle(game_recs)
        game = game_recs[self.index]
        self.index += 1

        author = self.bot.get_user(int(game["author"]))

        # Creating and formatting Embed
        embed = discord.Embed(color=discord.Colour.blue())
        if author is not None:
            embed.set_author(name=author.name, icon_url=author.display_avatar.url)
        embed.set_image(url=game["image"])
        embed.add_field(name=f"Recommendation: {game['title']}\n{game['link']}", value=game["description"])

        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Loads the RecommendGame cog."""
    await bot.add_cog(RecommendGame(bot))

import logging
from json import load
from pathlib import Path
import random

import discord
from discord.ext import commands


log = logging.getLogger(__name__)

emoji = [":heart:", ":couple_with_heart:", ":gift_heart: :revolving_hearts:", ":sparkling_heart:", ":two_hearts:" ]

class SaveTheDate:
    """
    A cog to change a invokers nickname to a spooky one!
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def savethedate(self, ctx):
        with open(Path('bot', 'resources', 'valentines', 'date_ideas.json'), 'r', encoding="utf8") as f:
            data = load(f)
            date_idea = random.choice(data['ideas'])
            emoji_1 = random.choice(emoji)
            emoji_2 = random.choice(emoji)
            embed = discord.Embed(title=date_idea['name'],
                                  description=f"{emoji_1}{date_idea['description']}{emoji_2}",
                                  colour=0x01d277)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(SaveTheDate(bot))
    log.debug("Save the date cog loaded")

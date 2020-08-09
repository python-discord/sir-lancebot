import json
import logging
import random
from pathlib import Path
from discord import Embed

from discord.ext import commands

log = logging.getLogger(__name__)

with open(Path("bot/resources/easter/starter.json"), "r", encoding="utf8") as f:
    starters = json.load(f)

with open(Path("bot/resources/easter/py_topics.json"), "r", encoding="utf8") as f:
    # First ID is #python-general and the rest are top to bottom categories of Topical Chat/Help.
    py_topics = json.load(f)


class ConvoStarters(commands.Cog):
    """Easter conversation topics."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def topic(self, ctx: commands.Context) -> None:
        """Responds with a random topic to start a conversation, changing depending on channel."""   

        # Fetching topics.
        channel_topics = py_topic[str(ctx.channel.id)]
        
        if channel_topics:
            return await ctx.send(random.choice(channel_topics['python-channels']))

        else:
            # If the channel ID doesn't have any topics.
            embed = Embed(
                description=(
                    "No topics found. You can suggest new ideas for topics "
                    "[here](https://github.com/python-discord/seasonalbot/issues/426)!"
                ))
            
            return await ctx.send(embed=embed)

        # If the channel isn't Python.
        await ctx.send(random.choice(starters['starters']))


def setup(bot: commands.Bot) -> None:
    """Conversation starters Cog load."""
    bot.add_cog(ConvoStarters(bot))

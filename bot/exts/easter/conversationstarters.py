import json
import logging
import random
from pathlib import Path

from discord import Embed
from discord.ext import commands

from bot.utils.decorators import override_in_channel


log = logging.getLogger(__name__)


with open(Path("bot/resources/easter/starter.json"), "r", encoding="utf8") as f:
    starters = json.load(f)

with open(Path("bot/resources/easter/py_topics.json"), "r", encoding="utf8") as f:
    # First ID is #python-general and the rest are top to bottom categories of Topical Chat/Help.
    py_topics = json.load(f)["python-channels"]
    all_python_channels = [int(channel_id) for channel_id in py_topics.keys()]


class ConvoStarters(commands.Cog):
    """Easter conversation topics."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @override_in_channel(all_python_channels)
    async def topic(self, ctx: commands.Context) -> None:
        """Responds with a random topic to start a conversation, changing depending on channel."""
        try:
            # Fetching topics.
            channel_topics = py_topics[str(ctx.channel.id)]

            if channel_topics:
                return await ctx.send(random.choice(channel_topics))

            # If the channel ID doesn't have any topics.
            else:
                embed = Embed(
                    description=(
                        "No topics found for this Python channel. You can suggest new ideas for topics "
                        "[here](https://github.com/python-discord/seasonalbot/issues/426)!"
                    ))

                return await ctx.send(embed=embed)

        except KeyError:
            # If the channel isn't Python.
            await ctx.send(random.choice(starters['starters']))


def setup(bot: commands.Bot) -> None:
    """Conversation starters Cog load."""
    bot.add_cog(ConvoStarters(bot))

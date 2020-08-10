import json
import random
from pathlib import Path

from discord import Embed
from discord.ext import commands

from bot.utils.decorators import override_in_channel


with Path("bot/resources/easter/starter.json").open("r", encoding="utf8") as f:
    STARTERS = json.load(f)["starters"]


with Path("bot/resources/easter/py_topics.json").open("r", encoding="utf8") as f:
    # First ID is #python-general and the rest are top to bottom categories of Topical Chat/Help.
    PY_TOPICS = json.load(f)["python-channels"]
    ALL_PYTHON_CHANNELS = [int(channel_id) for channel_id in PY_TOPICS.keys()]


class ConvoStarters(commands.Cog):
    """Easter conversation topics."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @override_in_channel(ALL_PYTHON_CHANNELS)
    async def topic(self, ctx: commands.Context) -> None:
        """Responds with a random topic to start a conversation, changing depending on channel."""
        try:
            # Fetching topics.
            channel_topics = PY_TOPICS[str(ctx.channel.id)]

        # If the channel isn't Python-related.
        except KeyError:
            await ctx.send(random.choice(STARTERS))

        # If the channel ID doesn't have any topics.
        else:
            if channel_topics:
                await ctx.send(random.choice(channel_topics))

            else:
                embed = Embed(
                    description=(
                        "No topics found for this Python channel. You can suggest new ideas for topics "
                        "[here](https://github.com/python-discord/seasonalbot/issues/426)!"
                    ))

                await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Conversation starters Cog load."""
    bot.add_cog(ConvoStarters(bot))

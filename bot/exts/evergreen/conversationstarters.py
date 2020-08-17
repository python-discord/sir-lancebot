import json
import random
from pathlib import Path

import yaml
from discord import Color, Embed
from discord.ext import commands

from bot.constants import WHITELISTED_CHANNELS
from bot.utils.decorators import override_in_channel


with Path("bot/resources/evergreen/starter.json").open("r", encoding="utf8") as f:
    STARTERS = json.load(f)["starters"]


with Path("bot/resources/evergreen/py_topics.yaml").open("r", encoding="utf8") as f:
    # First ID is #python-general and the rest are top to bottom categories of Topical Chat/Help.
    PY_TOPICS = yaml.load(f, Loader=yaml.FullLoader)

    # Removing `None` from lists of topics, if not a list, it is changed to an empty one.
    PY_TOPICS = {k: [i for i in v if i] if isinstance(v, list) else [] for k, v in PY_TOPICS.items()}

    # All the allowed channels that the ".topic" command is allowed to be executed in.
    ALL_ALLOWED_CHANNELS = [channel_id for channel_id in PY_TOPICS.keys()] + list(WHITELISTED_CHANNELS)


class ConvoStarters(commands.Cog):
    """Evergreen conversation topics."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @override_in_channel(ALL_ALLOWED_CHANNELS)
    async def topic(self, ctx: commands.Context) -> None:
        """
        Responds with a random topic to start a conversation.

        If in a Python channel, a python-related topic will be given.

        Otherwise, a random conversation topic will be recieved by the user.
        """
        try:
            # Fetching topics.
            channel_topics = PY_TOPICS[ctx.channel.id]

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
                    ),
                    color=Color.blurple()
                )

                await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Conversation starters Cog load."""
    bot.add_cog(ConvoStarters(bot))

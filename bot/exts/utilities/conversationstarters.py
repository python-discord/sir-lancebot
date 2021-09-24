from pathlib import Path

import yaml
from discord import Color, Embed
from discord.ext import commands

from bot.bot import Bot
from bot.constants import WHITELISTED_CHANNELS
from bot.utils.decorators import whitelist_override
from bot.utils.randomization import RandomCycle

SUGGESTION_FORM = "https://forms.gle/zw6kkJqv8U43Nfjg9"

with Path("bot/resources/utilities/starter.yaml").open("r", encoding="utf8") as f:
    STARTERS = yaml.load(f, Loader=yaml.FullLoader)

with Path("bot/resources/utilities/py_topics.yaml").open("r", encoding="utf8") as f:
    # First ID is #python-general and the rest are top to bottom categories of Topical Chat/Help.
    PY_TOPICS = yaml.load(f, Loader=yaml.FullLoader)

    # Removing `None` from lists of topics, if not a list, it is changed to an empty one.
    PY_TOPICS = {k: [i for i in v if i] if isinstance(v, list) else [] for k, v in PY_TOPICS.items()}

    # All the allowed channels that the ".topic" command is allowed to be executed in.
    ALL_ALLOWED_CHANNELS = list(PY_TOPICS.keys()) + list(WHITELISTED_CHANNELS)

# Putting all topics into one dictionary and shuffling lists to reduce same-topic repetitions.
ALL_TOPICS = {"default": STARTERS, **PY_TOPICS}
TOPICS = {
    channel: RandomCycle(topics or ["No topics found for this channel."])
    for channel, topics in ALL_TOPICS.items()
}


class ConvoStarters(commands.Cog):
    """General conversation topics."""

    @commands.command()
    @commands.cooldown(1, 60*2, commands.BucketType.channel)
    @whitelist_override(channels=ALL_ALLOWED_CHANNELS)
    async def topic(self, ctx: commands.Context) -> None:
        """
        Responds with a random topic to start a conversation.

        Allows the refresh of a topic by pressing an emoji.
        """
        message = await ctx.send(embed=self._build_topic_embed(ctx.channel.id))
        self.bot.loop.create_task(self._listen_for_refresh(message))


def setup(bot: Bot) -> None:
    """Load the ConvoStarters cog."""
    bot.add_cog(ConvoStarters())

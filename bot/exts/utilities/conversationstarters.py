from contextlib import suppress
from functools import partial
from pathlib import Path

import discord
import yaml
from discord.ext import commands

from bot.bot import Bot
from bot.constants import MODERATION_ROLES, WHITELISTED_CHANNELS
from bot.utils.decorators import whitelist_override
from bot.utils.randomization import RandomCycle

SUGGESTION_FORM = "https://forms.gle/zw6kkJqv8U43Nfjg9"

with Path("bot/resources/utilities/starter.yaml").open("r", encoding="utf8") as f:
    STARTERS = yaml.safe_load(f)

with Path("bot/resources/utilities/py_topics.yaml").open("r", encoding="utf8") as f:
    # First ID is #python-general and the rest are top to bottom categories of Topical Chat/Help.
    PY_TOPICS = yaml.safe_load(f)

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

    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def _build_topic_embed(channel_id: int, previous_description: None | str) -> tuple[discord.Embed, bool]:
        """
        Build an embed containing a conversation topic.

        If in a Python channel, a python-related topic will be given.
        Otherwise, a random conversation topic will be received by the user.

        Also returns a value that determines whether to remove the reaction afterwards
        """
        footer = f"Suggest more topics [here]({SUGGESTION_FORM})!"
        max_topics = 3

        # Remove footer from previous description
        previous_topic = None
        if previous_description:
            previous_topic = previous_description.split("\n\n")[0]

        embed = discord.Embed(
            title="Conversation Starter",
            color=discord.Colour.og_blurple()
        )

        try:
            channel_topics = TOPICS[str(channel_id)]
        except KeyError:
            # Channel doesn't have any topics.
            new_topic = next(TOPICS["default"])
        else:
            new_topic = next(channel_topics)

        def add_description(text: str) -> None:
            embed.description = f"{text}\n\n{footer}"

        if previous_topic is None:
            # This is the first topic being sent
            add_description(new_topic)
            return embed, False

        total_topics = previous_topic.count("\n") + 1

        # Handle forced reactions after clear
        if total_topics >= max_topics:
            embed.description = previous_description
            return embed, True

        # Add 1 before first topic
        if total_topics == 1:
            previous_topic = f"1. {previous_topic}"

        add_description(f"{previous_topic}\n{total_topics + 1}. {new_topic}")

        # If this is the last topic, remove the reaction
        if total_topics == max_topics - 1:
            return embed, True
        return embed, False

    @staticmethod
    def _predicate(
        command_invoker: discord.User | discord.Member,
        message: discord.Message,
        reaction: discord.Reaction,
        user: discord.User
    ) -> bool:
        user_is_moderator = any(role.id in MODERATION_ROLES for role in getattr(user, "roles", []))
        user_is_invoker = user.id == command_invoker.id

        is_right_reaction = all((
            reaction.message.id == message.id,
            str(reaction.emoji) == "🔄",
            user_is_moderator or user_is_invoker
        ))
        return is_right_reaction

    async def _listen_for_refresh(
        self,
        command_invoker: discord.User | discord.Member,
        message: discord.Message
    ) -> None:
        await message.add_reaction("🔄")
        while True:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add",
                    check=partial(self._predicate, command_invoker, message),
                    timeout=60.0
                )
            except TimeoutError:
                with suppress(discord.NotFound):
                    await message.clear_reaction("🔄")
                break

            try:
                # The returned discord.Message object from discord.Message.edit is different from the current
                # discord.Message object, so it must be reassigned to update properly
                embed, remove_reactions = self._build_topic_embed(message.channel.id, message.embeds[0].description)
                message = await message.edit(embed=embed)
                if remove_reactions:
                    await message.clear_reaction("🔄")
            except discord.NotFound:
                break

            with suppress(discord.NotFound):
                await message.remove_reaction(reaction, user)

    @commands.command()
    @commands.cooldown(1, 60 * 2, commands.BucketType.channel)
    @whitelist_override(channels=ALL_ALLOWED_CHANNELS)
    async def topic(self, ctx: commands.Context) -> None:
        """
        Responds with a random topic to start a conversation.

        Allows the refresh of a topic by pressing an emoji.
        """
        message = await ctx.send(embed=self._build_topic_embed(ctx.channel.id, None)[0])
        self.bot.loop.create_task(self._listen_for_refresh(ctx.author, message))


async def setup(bot: Bot) -> None:
    """Load the ConvoStarters cog."""
    await bot.add_cog(ConvoStarters(bot))

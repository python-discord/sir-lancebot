import logging
import random
from typing import Union

import discord
from async_rediscache import RedisCache
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Channels, Month
from bot.utils.decorators import in_month

log = logging.getLogger(__name__)

# chance is 1 in x range, so 1 in 20 range would give 5% chance (for add candy)
ADD_CANDY_REACTION_CHANCE = 20  # 5%
ADD_CANDY_EXISTING_REACTION_CHANCE = 10  # 10%
ADD_SKULL_REACTION_CHANCE = 50  # 2%
ADD_SKULL_EXISTING_REACTION_CHANCE = 20  # 5%

EMOJIS = dict(
    CANDY="\N{CANDY}",
    SKULL="\N{SKULL}",
    MEDALS=(
        "\N{FIRST PLACE MEDAL}",
        "\N{SECOND PLACE MEDAL}",
        "\N{THIRD PLACE MEDAL}",
        "\N{SPORTS MEDAL}",
        "\N{SPORTS MEDAL}",
    ),
)


class CandyCollection(commands.Cog):
    """Candy collection game Cog."""

    # User candy amount records
    candy_records = RedisCache()

    # Candy and skull messages mapping
    candy_messages = RedisCache()
    skull_messages = RedisCache()

    def __init__(self, bot: Bot):
        self.bot = bot

    @in_month(Month.OCTOBER)
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Randomly adds candy or skull reaction to non-bot messages in the Event channel."""
        # Ignore messages in DMs
        if not message.guild:
            return
        # make sure its a human message
        if message.author.bot:
            return
        # ensure it's hacktober channel
        if message.channel.id != Channels.sir_lancebot_playground:
            return

        # do random check for skull first as it has the lower chance
        if random.randint(1, ADD_SKULL_REACTION_CHANCE) == 1:
            await self.skull_messages.set(message.id, "skull")
            await message.add_reaction(EMOJIS["SKULL"])
        # check for the candy chance next
        elif random.randint(1, ADD_CANDY_REACTION_CHANCE) == 1:
            await self.candy_messages.set(message.id, "candy")
            await message.add_reaction(EMOJIS["CANDY"])

    @in_month(Month.OCTOBER)
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: Union[discord.User, discord.Member]) -> None:
        """Add/remove candies from a person if the reaction satisfies criteria."""
        message = reaction.message
        # check to ensure the reactor is human
        if user.bot:
            return

        # check to ensure it is in correct channel
        if message.channel.id != Channels.sir_lancebot_playground:
            return

        # if its not a candy or skull, and it is one of 10 most recent messages,
        # proceed to add a skull/candy with higher chance
        if str(reaction.emoji) not in (EMOJIS["SKULL"], EMOJIS["CANDY"]):
            # Ensure the reaction is not for a bot's message so users can't spam
            # reaction buttons like in .help to get candies.
            if message.author.bot:
                return

            recent_message_ids = map(
                lambda m: m.id,
                await self.hacktober_channel.history(limit=10).flatten()
            )
            if message.id in recent_message_ids:
                await self.reacted_msg_chance(message)
            return

        if await self.candy_messages.get(message.id) == "candy" and str(reaction.emoji) == EMOJIS["CANDY"]:
            await self.candy_messages.delete(message.id)
            if await self.candy_records.contains(user.id):
                await self.candy_records.increment(user.id)
            else:
                await self.candy_records.set(user.id, 1)

        elif await self.skull_messages.get(message.id) == "skull" and str(reaction.emoji) == EMOJIS["SKULL"]:
            await self.skull_messages.delete(message.id)

            if prev_record := await self.candy_records.get(user.id):
                lost = min(random.randint(1, 3), prev_record)
                await self.candy_records.decrement(user.id, lost)

                if lost == prev_record:
                    await CandyCollection.send_spook_msg(user, message.channel, "all of your")
                else:
                    await CandyCollection.send_spook_msg(user, message.channel, lost)
            else:
                await CandyCollection.send_no_candy_spook_message(user, message.channel)
        else:
            return  # Skip saving

        await reaction.clear()

    async def reacted_msg_chance(self, message: discord.Message) -> None:
        """
        Randomly add a skull or candy reaction to a message if there is a reaction there already.

        This event has a higher probability of occurring than a reaction add to a message without an
        existing reaction.
        """
        if random.randint(1, ADD_SKULL_EXISTING_REACTION_CHANCE) == 1:
            await self.skull_messages.set(message.id, "skull")
            await message.add_reaction(EMOJIS["SKULL"])

        elif random.randint(1, ADD_CANDY_EXISTING_REACTION_CHANCE) == 1:
            await self.candy_messages.set(message.id, "candy")
            await message.add_reaction(EMOJIS["CANDY"])

    @property
    def hacktober_channel(self) -> discord.TextChannel:
        """Get #hacktoberbot channel from its ID."""
        return self.bot.get_channel(Channels.sir_lancebot_playground)

    @staticmethod
    async def send_spook_msg(
        author: discord.Member, channel: discord.TextChannel, candies: Union[str, int]
    ) -> None:
        """Send a spooky message."""
        e = discord.Embed(colour=author.colour)
        e.set_author(
            name="Ghosts and Ghouls and Jack o' lanterns at night; "
            f"I took {candies} candies and quickly took flight."
        )
        await channel.send(embed=e)

    @staticmethod
    async def send_no_candy_spook_message(
        author: discord.Member,
        channel: discord.TextChannel
    ) -> None:
        """An alternative spooky message sent when user has no candies in the collection."""
        embed = discord.Embed(color=author.color)
        embed.set_author(
            name=(
                "Ghosts and Ghouls and Jack o' lanterns at night; "
                "I tried to take your candies but you had none to begin with!"
            )
        )
        await channel.send(embed=embed)

    @in_month(Month.OCTOBER)
    @commands.command()
    async def candy(self, ctx: commands.Context) -> None:
        """Get the candy leaderboard and save to JSON."""
        records = await self.candy_records.items()

        def generate_leaderboard() -> str:
            top_sorted = sorted(
                ((user_id, score) for user_id, score in records if score > 0),
                key=lambda x: x[1],
                reverse=True
            )
            top_five = top_sorted[:5]

            return "\n".join(
                f"{EMOJIS['MEDALS'][index]} <@{record[0]}>: {record[1]}"
                for index, record in enumerate(top_five)
            ) if top_five else "No Candies"

        def get_user_candy_score() -> str:
            for user_id, score in records:
                if user_id == ctx.author.id:
                    return f"{ctx.author.mention}: {score}"
            return f"{ctx.author.mention}: 0"

        e = discord.Embed(colour=discord.Colour.og_blurple())
        e.add_field(
            name="Top Candy Records",
            value=generate_leaderboard(),
            inline=False
        )
        e.add_field(
            name="Your Candy Score",
            value=get_user_candy_score(),
            inline=False
        )
        e.add_field(
            name="\u200b",
            value="Candies will randomly appear on messages sent. "
                  "\nHit the candy when it appears as fast as possible to get the candy! "
                  "\nBut beware the ghosts...",
            inline=False
        )
        await ctx.send(embed=e)


def setup(bot: Bot) -> None:
    """Load the Candy Collection Cog."""
    bot.add_cog(CandyCollection(bot))

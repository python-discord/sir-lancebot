import json
import logging
import random
from pathlib import Path
from typing import Union

import discord
from discord.ext import commands

from bot.constants import Channels, Month
from bot.utils.decorators import in_month
from bot.utils.persist import make_persistent

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
        '\N{FIRST PLACE MEDAL}',
        '\N{SECOND PLACE MEDAL}',
        '\N{THIRD PLACE MEDAL}',
        '\N{SPORTS MEDAL}',
        '\N{SPORTS MEDAL}',
    ),
)


class CandyCollection(commands.Cog):
    """Candy collection game Cog."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.json_file = make_persistent(Path("bot", "resources", "halloween", "candy_collection.json"))

        with self.json_file.open() as fp:
            candy_data = json.load(fp)

        self.candy_records = candy_data.get("records", dict())

        # Message ID where bot added the candies/skulls
        self.candy_messages = set()
        self.skull_messages = set()

    @in_month(Month.OCTOBER)
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Randomly adds candy or skull reaction to non-bot messages in the Event channel."""
        # make sure its a human message
        if message.author.bot:
            return
        # ensure it's hacktober channel
        if message.channel.id != Channels.seasonalbot_commands:
            return

        # do random check for skull first as it has the lower chance
        if random.randint(1, ADD_SKULL_REACTION_CHANCE) == 1:
            self.skull_messages.add(message.id)
            return await message.add_reaction(EMOJIS['SKULL'])
        # check for the candy chance next
        if random.randint(1, ADD_CANDY_REACTION_CHANCE) == 1:
            self.candy_messages.add(message.id)
            return await message.add_reaction(EMOJIS['CANDY'])

    @in_month(Month.OCTOBER)
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member) -> None:
        """Add/remove candies from a person if the reaction satisfies criteria."""
        message = reaction.message
        # check to ensure the reactor is human
        if user.bot:
            return

        # check to ensure it is in correct channel
        if message.channel.id != Channels.seasonalbot_commands:
            return

        # if its not a candy or skull, and it is one of 10 most recent messages,
        # proceed to add a skull/candy with higher chance
        if str(reaction.emoji) not in (EMOJIS['SKULL'], EMOJIS['CANDY']):
            recent_message_ids = map(
                lambda m: m.id,
                await self.hacktober_channel.history(limit=10).flatten()
            )
            if message.id in recent_message_ids:
                await self.reacted_msg_chance(message)
            return

        if message.id in self.candy_messages and str(reaction.emoji) == EMOJIS['CANDY']:
            self.candy_messages.remove(message.id)
            prev_record = self.candy_records.get(str(user.id), 0)
            self.candy_records[str(user.id)] = prev_record + 1

        elif message.id in self.skull_messages and str(reaction.emoji) == EMOJIS['SKULL']:
            self.skull_messages.remove(message.id)

            if prev_record := self.candy_records.get(str(user.id)):
                lost = min(random.randint(1, 3), prev_record)
                self.candy_records[str(user.id)] = prev_record - lost

                if lost == prev_record:
                    await CandyCollection.send_spook_msg(user, message.channel, 'all of your')
                else:
                    await CandyCollection.send_spook_msg(user, message.channel, lost)
            else:
                await CandyCollection.send_no_candy_spook_message(user, message.channel)
        else:
            return  # Skip saving

        await reaction.clear()
        await self.bot.loop.run_in_executor(None, self.save_to_json)

    async def reacted_msg_chance(self, message: discord.Message) -> None:
        """
        Randomly add a skull or candy reaction to a message if there is a reaction there already.

        This event has a higher probability of occurring than a reaction add to a message without an
        existing reaction.
        """
        if random.randint(1, ADD_SKULL_EXISTING_REACTION_CHANCE) == 1:
            self.skull_messages.add(message.id)
            return await message.add_reaction(EMOJIS['SKULL'])

        if random.randint(1, ADD_CANDY_EXISTING_REACTION_CHANCE) == 1:
            self.candy_messages.add(message.id)
            return await message.add_reaction(EMOJIS['CANDY'])

    @property
    def hacktober_channel(self) -> discord.TextChannel:
        """Get #hacktoberbot channel from its ID."""
        return self.bot.get_channel(id=Channels.seasonalbot_commands)

    @staticmethod
    async def send_spook_msg(
        author: discord.Member, channel: discord.TextChannel, candies: Union[str, int]
    ) -> None:
        """Send a spooky message."""
        e = discord.Embed(colour=author.colour)
        e.set_author(name="Ghosts and Ghouls and Jack o' lanterns at night; "
                          f"I took {candies} candies and quickly took flight.")
        await channel.send(embed=e)

    @staticmethod
    async def send_no_candy_spook_message(
        author: discord.Member,
        channel: discord.TextChannel
    ) -> None:
        """An alternative spooky message sent when user has no candies in the collection."""
        embed = discord.Embed(color=author.color)
        embed.set_author(name="Ghosts and Ghouls and Jack o' lanterns at night; "
                              "I tried to take your candies but you had none to begin with!")
        await channel.send(embed=embed)

    def save_to_json(self) -> None:
        """Save JSON to a local file."""
        with self.json_file.open('w') as fp:
            json.dump(dict(records=self.candy_records), fp)

    @in_month(Month.OCTOBER)
    @commands.command()
    async def candy(self, ctx: commands.Context) -> None:
        """Get the candy leaderboard and save to JSON."""
        def generate_leaderboard() -> str:
            top_sorted = sorted(
                ((user_id, score) for user_id, score in self.candy_records.items() if score > 0),
                key=lambda x: x[1],
                reverse=True
            )
            top_five = top_sorted[:5]

            return '\n'.join(
                f"{EMOJIS['MEDALS'][index]} <@{record[0]}>: {record[1]}"
                for index, record in enumerate(top_five)
            ) if top_five else 'No Candies'

        e = discord.Embed(colour=discord.Colour.blurple())
        e.add_field(
            name="Top Candy Records",
            value=generate_leaderboard(),
            inline=False
        )
        e.add_field(
            name='\u200b',
            value="Candies will randomly appear on messages sent. "
                  "\nHit the candy when it appears as fast as possible to get the candy! "
                  "\nBut beware the ghosts...",
            inline=False
        )
        await ctx.send(embed=e)


def setup(bot: commands.Bot) -> None:
    """Candy Collection game Cog load."""

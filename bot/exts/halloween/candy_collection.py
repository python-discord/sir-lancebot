import json
import logging
import os
import random
from typing import List, Union

import discord
from discord.ext import commands

from bot.constants import Channels, Month
from bot.utils.decorators import in_month

log = logging.getLogger(__name__)

json_location = os.path.join("bot", "resources", "halloween", "candy_collection.json")

# chance is 1 in x range, so 1 in 20 range would give 5% chance (for add candy)
ADD_CANDY_REACTION_CHANCE = 20  # 5%
ADD_CANDY_EXISTING_REACTION_CHANCE = 10  # 10%
ADD_SKULL_REACTION_CHANCE = 50  # 2%
ADD_SKULL_EXISTING_REACTION_CHANCE = 20  # 5%


class CandyCollection(commands.Cog):
    """Candy collection game Cog."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        with open(json_location, encoding="utf8") as candy:
            candy_data = json.load(candy)

        # The rank data
        self.candy_records = candy_data.get("records") or dict()

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
            return await message.add_reaction('\N{SKULL}')
        # check for the candy chance next
        if random.randint(1, ADD_CANDY_REACTION_CHANCE) == 1:
            self.candy_messages.add(message.id)
            return await message.add_reaction('\N{CANDY}')

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
        if str(reaction.emoji) not in ('\N{SKULL}', '\N{CANDY}'):
            if message.id in await self.ten_recent_msg():
                await self.reacted_msg_chance(message)
            return

        if message.id in self.candy_messages and str(reaction.emoji) == '\N{CANDY}':
            self.candy_messages.remove(message.id)
            prev_record = self.candy_records.get(str(message.author.id)) or 0
            self.candy_records[str(message.author.id)] = prev_record + 1

        elif message.id in self.skull_messages and str(reaction.emoji) == '\N{SKULL}':
            self.skull_messages.remove(message.id)

            if (prev_record := self.candy_records.get(str(message.author.id))) is not None:
                lost = min(random.randint(1, 3), prev_record)
                self.candy_records[str(message.author.id)] = prev_record - lost

                if lost == prev_record:
                    await self.send_spook_msg(message.author, message.channel, 'all of your')
                else:
                    await self.send_spook_msg(message.author, message.channel, lost)
        else:
            return  # Skip saving

        await self.remove_reactions(reaction)
        await self.bot.loop.run_in_executor(None, self.save_to_json)

    async def reacted_msg_chance(self, message: discord.Message) -> None:
        """
        Randomly add a skull or candy reaction to a message if there is a reaction there already.

        This event has a higher probability of occurring than a reaction add to a message without an
        existing reaction.
        """
        if random.randint(1, ADD_SKULL_EXISTING_REACTION_CHANCE) == 1:
            self.skull_messages.add(message.id)
            return await message.add_reaction('\N{SKULL}')

        if random.randint(1, ADD_CANDY_EXISTING_REACTION_CHANCE) == 1:
            self.candy_messages.add(message.id)
            return await message.add_reaction('\N{CANDY}')

    async def ten_recent_msg(self) -> List[int]:
        """Get the last 10 messages sent in the channel."""
        ten_recent = []
        recent_msg_id = max(
            message.id for message in self.bot._connection._messages
            if message.channel.id == Channels.seasonalbot_commands
        )

        channel = await self.hacktober_channel()
        ten_recent.append(recent_msg_id)

        for i in range(9):
            o = discord.Object(id=recent_msg_id + i)
            msg = await next(channel.history(limit=1, before=o))
            ten_recent.append(msg.id)

        return ten_recent

    async def get_message(self, msg_id: int) -> Union[discord.Message, None]:
        """Get the message from its ID."""
        try:
            o = discord.Object(id=msg_id + 1)
            # Use history rather than get_message due to
            #         poor ratelimit (50/1s vs 1/1s)
            msg = await next(self.hacktober_channel.history(limit=1, before=o))

            if msg.id != msg_id:
                return None

            return msg

        except Exception:
            return None

    async def hacktober_channel(self) -> discord.TextChannel:
        """Get #hacktoberbot channel from its ID."""
        return self.bot.get_channel(id=Channels.seasonalbot_commands)

    async def remove_reactions(self, reaction: discord.Reaction) -> None:
        """Remove all candy/skull reactions."""
        try:
            async for user in reaction.users():
                await reaction.message.remove_reaction(reaction.emoji, user)

        except discord.HTTPException:
            pass

    async def send_spook_msg(self, author: discord.Member, channel: discord.TextChannel, candies: int) -> None:
        """Send a spooky message."""
        e = discord.Embed(colour=author.colour)
        e.set_author(name="Ghosts and Ghouls and Jack o' lanterns at night; "
                          f"I took {candies} candies and quickly took flight.")
        await channel.send(embed=e)

    def save_to_json(self) -> None:
        """Save JSON to a local file."""
        with open(json_location, 'w', encoding="utf8") as outfile:
            json.dump(dict(records=self.candy_records), outfile)

    @in_month(Month.OCTOBER)
    @commands.command()
    async def candy(self, ctx: commands.Context) -> None:
        """Get the candy leaderboard and save to JSON."""
        emoji = (
            '\N{FIRST PLACE MEDAL}',
            '\N{SECOND PLACE MEDAL}',
            '\N{THIRD PLACE MEDAL}',
            '\N{SPORTS MEDAL}',
            '\N{SPORTS MEDAL}'
        )

        top_sorted = sorted(((user_id, score) for user_id, score in self.candy_records.items()),
                            key=lambda x: x[1], reverse=True)
        top_five = top_sorted[:5]

        leaderboard = '\n'.join(f"{emoji[index]} <@{record[0]}>: {record[1]}"
                                for index, record in enumerate(top_five)) or 'No Candies'

        e = discord.Embed(colour=discord.Colour.blurple())
        e.add_field(name="Top Candy Records", value=leaderboard, inline=False)
        e.add_field(name='\u200b',
                    value="Candies will randomly appear on messages sent. "
                          "\nHit the candy when it appears as fast as possible to get the candy! "
                          "\nBut beware the ghosts...",
                    inline=False)
        await ctx.send(embed=e)


def setup(bot: commands.Bot) -> None:
    """Candy Collection game Cog load."""
    bot.add_cog(CandyCollection(bot))

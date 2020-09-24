import functools
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
            self.candy_json = json.load(candy)
            self.msg_reacted = self.candy_json['msg_reacted']
        self.get_candyinfo = dict()
        for userinfo in self.candy_json['records']:
            userid = userinfo['userid']
            self.get_candyinfo[userid] = userinfo

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
            d = {"reaction": '\N{SKULL}', "msg_id": message.id, "won": False}
            self.msg_reacted.append(d)
            return await message.add_reaction('\N{SKULL}')
        # check for the candy chance next
        if random.randint(1, ADD_CANDY_REACTION_CHANCE) == 1:
            d = {"reaction": '\N{CANDY}', "msg_id": message.id, "won": False}
            self.msg_reacted.append(d)
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

        for react in self.msg_reacted:
            # check to see if the message id of a message we added a
            # reaction to is in json file, and if nobody has won/claimed it yet
            if react['msg_id'] == message.id and react['won'] is False:
                react['user_reacted'] = user.id
                react['won'] = True
                try:
                    # if they have record/candies in json already it will do this
                    user_records = self.get_candyinfo[user.id]
                    if str(reaction.emoji) == '\N{CANDY}':
                        user_records['record'] += 1
                    if str(reaction.emoji) == '\N{SKULL}':
                        if user_records['record'] <= 3:
                            user_records['record'] = 0
                            lost = 'all of your'
                        else:
                            lost = random.randint(1, 3)
                            user_records['record'] -= lost
                        await self.send_spook_msg(message.author, message.channel, lost)

                except KeyError:
                    # otherwise it will raise KeyError so we need to add them to file
                    if str(reaction.emoji) == '\N{CANDY}':
                        print('ok')
                        d = {"userid": user.id, "record": 1}
                        self.candy_json['records'].append(d)
                await self.remove_reactions(reaction)

    async def reacted_msg_chance(self, message: discord.Message) -> None:
        """
        Randomly add a skull or candy reaction to a message if there is a reaction there already.

        This event has a higher probability of occurring than a reaction add to a message without an
        existing reaction.
        """
        if random.randint(1, ADD_SKULL_EXISTING_REACTION_CHANCE) == 1:
            d = {"reaction": '\N{SKULL}', "msg_id": message.id, "won": False}
            self.msg_reacted.append(d)
            return await message.add_reaction('\N{SKULL}')

        if random.randint(1, ADD_CANDY_EXISTING_REACTION_CHANCE) == 1:
            d = {"reaction": '\N{CANDY}', "msg_id": message.id, "won": False}
            self.msg_reacted.append(d)
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
            json.dump(self.candy_json, outfile)

    @in_month(Month.OCTOBER)
    @commands.command()
    async def candy(self, ctx: commands.Context) -> None:
        """Get the candy leaderboard and save to JSON."""
        # Use run_in_executor to prevent blocking
        thing = functools.partial(self.save_to_json)
        await self.bot.loop.run_in_executor(None, thing)

        emoji = (
            '\N{FIRST PLACE MEDAL}',
            '\N{SECOND PLACE MEDAL}',
            '\N{THIRD PLACE MEDAL}',
            '\N{SPORTS MEDAL}',
            '\N{SPORTS MEDAL}'
        )

        top_sorted = sorted(self.candy_json['records'], key=lambda k: k.get('record', 0), reverse=True)
        top_five = top_sorted[:5]

        usersid = []
        records = []
        for record in top_five:
            usersid.append(record['userid'])
            records.append(record['record'])

        value = '\n'.join(f'{emoji[index]} <@{usersid[index]}>: {records[index]}'
                          for index in range(0, len(usersid))) or 'No Candies'

        e = discord.Embed(colour=discord.Colour.blurple())
        e.add_field(name="Top Candy Records", value=value, inline=False)
        e.add_field(name='\u200b',
                    value="Candies will randomly appear on messages sent. "
                          "\nHit the candy when it appears as fast as possible to get the candy! "
                          "\nBut beware the ghosts...",
                    inline=False)
        await ctx.send(embed=e)


def setup(bot: commands.Bot) -> None:
    """Candy Collection game Cog load."""
    bot.add_cog(CandyCollection(bot))

import asyncio
import json
import logging
import random
from pathlib import Path

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES

log = logging.getLogger(__name__)

TIME_LIMIT = 60

# Issue with the json file , gotta try it on local environment first
with open(Path("bot/resources/fun/anagram.json")) as f:
    ANAGRAMS_ALL = json.loads(f.read_text("utf8"))


class Anagram(commands.Cog):
    """Cog for the Anagram game command."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.winners = set()
        self.correct = ""
        self.current_channel = None

    @commands.command(name="anagram", aliases=("anag", "gram", "ag"))
    async def anagram_command(self, ctx: commands.Context) -> None:
        """
        Given shuffled letters which can be rearranged to form Anagrams.

        If this works correctly will update this more in detail
        """
        if self.current_channel:
            await ctx.send(f"An anagram is already being solved in {self.current_channel.mention}!")
            return

        # Don't let users start in a DM
        if not ctx.guild:
            await ctx.send(
                embed=discord.Embed(
                    title=random.choice(NEGATIVE_REPLIES),
                    description="You can't start riddles in DMs",
                    colour=discord.Colour.red()
                )
            )
            return

        self.current_channel = ctx.channel

        anagram_letters, anagram_answers = random.choice(list(ANAGRAMS_ALL.items()))
        scrambled_letters = anagram_letters
        self.correct = anagram_answers

        embed_title = f"Find anagrams from these letters '{scrambled_letters.upper()}'"
        embed_description = f"You have {TIME_LIMIT} seconds to find all words."

        anagram_embed = discord.Embed(title=embed_title, description=embed_description, colour=Colours.purple)

        await ctx.send(embed=anagram_embed)
        await asyncio.sleep(TIME_LIMIT)

        if self.winners:
            win_list = ", ".join(self.winners)
            content = f"Well done {win_list} for getting it right!"
        else:
            content = "Nobody got it right."

        answer_embed = discord.Embed(
            title=f"The words were:  `{'`, `'.join(anagram_answers)}`!",
            colour=Colours.pink
        )

        await ctx.send(content, embed=answer_embed)

        self.winners.clear()
        self.current_channel = None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """If a non-bot user enters a correct answer, their username gets added to self.winners."""
        if self.current_channel != message.channel:
            return

        if self.bot.user == message.author:
            return

        if message.content.lower() in self.correct:
            self.winners.add(message.author.mention)


def setup(bot: Bot) -> None:
    """Loads the Anagram cog."""
    bot.add_cog(Anagram(bot))

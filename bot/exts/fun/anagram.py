import asyncio
import json
import logging
import random
from pathlib import Path

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

log = logging.getLogger(__name__)

TIME_LIMIT = 60

# anagram.json file contains all the anagrams
with open(Path("bot/resources/fun/anagram.json"), "r") as f:
    ANAGRAMS_ALL = json.load(f)


class AnagramGame:
    """
    Used for creating instances of anagram games.

    Once multiple games can be run at the same time, this class' instances
    can be used for keeping track of each anagram game.
    """

    def __init__(self, scrambled: str, correct: list[str]) -> None:
        self.scrambled = scrambled
        self.correct = set(correct)

        self.winners = set()

    async def message_creation(self, message: discord.Message) -> None:
        """Check if the message is a correct answer and remove it from the list of answers."""
        if message.content.lower() in self.correct:
            self.winners.add(message.author.mention)
            self.correct.remove(message.content.lower())


class Anagram(commands.Cog):
    """Cog for the Anagram game command."""

    def __init__(self, bot: Bot):
        self.bot = bot

        self.games: dict[int, AnagramGame] = {}

    @commands.command(name="anagram", aliases=("anag", "gram", "ag"))
    async def anagram_command(self, ctx: commands.Context) -> None:
        """
        Given shuffled letters, rearrange them into anagrams.

        Show an embed with scrambled letters which if rearranged can form words.
        After a specific amount of time, list the correct answers and whether someone provided a
        correct answer.
        """
        if self.games.get(ctx.channel.id):
            await ctx.send("An anagram is already being solved in this channel!")
            return

        scrambled_letters, correct = random.choice(list(ANAGRAMS_ALL.items()))

        game = AnagramGame(scrambled_letters, correct)
        self.games[ctx.channel.id] = game

        anagram_embed = discord.Embed(
            title=f"Find anagrams from these letters: '{scrambled_letters.upper()}'",
            description=f"You have {TIME_LIMIT} seconds to find correct words.",
            colour=Colours.purple,
        )

        await ctx.send(embed=anagram_embed)
        await asyncio.sleep(TIME_LIMIT)

        if game.winners:
            win_list = ", ".join(game.winners)
            content = f"Well done {win_list} for getting it right!"
        else:
            content = "Nobody got it right."

        answer_embed = discord.Embed(
            title=f"The words were:  `{'`, `'.join(ANAGRAMS_ALL[game.scrambled])}`!",
            colour=Colours.pink,
        )

        await ctx.send(content, embed=answer_embed)

        # Game is finished, let's remove it from the dict
        self.games.pop(ctx.channel.id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Check a message for an anagram attempt and pass to an ongoing game."""
        if message.author.bot or not message.guild:
            return

        game = self.games.get(message.channel.id)
        if not game:
            return

        await game.message_creation(message)


async def setup(bot: Bot) -> None:
    """Load the Anagram cog."""
    await bot.add_cog(Anagram(bot))

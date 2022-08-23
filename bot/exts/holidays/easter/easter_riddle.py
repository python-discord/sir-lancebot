import asyncio
import logging
import random
from json import loads
from pathlib import Path

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES

log = logging.getLogger(__name__)

RIDDLE_QUESTIONS = loads(Path("bot/resources/holidays/easter/easter_riddle.json").read_text("utf8"))

TIMELIMIT = 10


class EasterRiddle(commands.Cog):
    """This cog contains the command for the Easter quiz!"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.winners = set()
        self.correct = ""
        self.current_channel = None

    @commands.command(aliases=("riddlemethis", "riddleme"))
    async def riddle(self, ctx: commands.Context) -> None:
        """
        Gives a random riddle, then provides 2 hints at certain intervals before revealing the answer.

        The duration of the hint interval can be configured by changing the TIMELIMIT constant in this file.
        """
        if self.current_channel:
            await ctx.send(f"A riddle is already being solved in {self.current_channel.mention}!")
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

        random_question = random.choice(RIDDLE_QUESTIONS)
        question = random_question["question"]
        hints = random_question["riddles"]
        self.correct = random_question["correct_answer"]

        description = f"You have {TIMELIMIT} seconds before the first hint."

        riddle_embed = discord.Embed(title=question, description=description, colour=Colours.pink)

        await ctx.send(embed=riddle_embed)
        await asyncio.sleep(TIMELIMIT)

        hint_embed = discord.Embed(
            title=f"Here's a hint: {hints[0]}!",
            colour=Colours.pink
        )

        await ctx.send(embed=hint_embed)
        await asyncio.sleep(TIMELIMIT)

        hint_embed = discord.Embed(
            title=f"Here's a hint: {hints[1]}!",
            colour=Colours.pink
        )

        await ctx.send(embed=hint_embed)
        await asyncio.sleep(TIMELIMIT)

        if self.winners:
            win_list = " ".join(self.winners)
            content = f"Well done {win_list} for getting it right!"
        else:
            content = "Nobody got it right..."

        answer_embed = discord.Embed(
            title=f"The answer is: {self.correct}!",
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

        if message.content.lower() == self.correct.lower():
            self.winners.add(message.author.mention)


async def setup(bot: Bot) -> None:
    """Easter Riddle Cog load."""
    await bot.add_cog(EasterRiddle(bot))

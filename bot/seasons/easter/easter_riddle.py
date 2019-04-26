import asyncio
import logging
import random
from json import load
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)

with open(Path('bot', 'resources', 'easter', 'easter_riddle.json'), 'r', encoding="utf8") as f:
    RIDDLE_QUESTIONS = load(f)

TIMELIMIT = 10


class EasterRiddle(commands.Cog):
    """This cog contains the command for the Easter quiz!"""

    def __init__(self, bot):
        self.bot = bot
        self.quiz_messages = {}
        self.winner = " "
        self.correct = ""

    @commands.command(aliases=["riddlemethis", "riddleme"])
    async def riddle(self, ctx):
        """
        Gives a random riddle questions, then provides 2 hints at 10 second intervals before revealing the answer

        """
        random_question = random.choice(RIDDLE_QUESTIONS)
        question, hints = random_question["question"], random_question["riddles"]
        self.correct = random_question["correct_answer"]

        description = f"You have {TIMELIMIT} seconds before the first hint.\n\n"

        q_embed = discord.Embed(title=question, description=description, colour=Colours.pink)

        await ctx.send(embed=q_embed)
        await asyncio.sleep(TIMELIMIT)

        h_embed = discord.Embed(
            title=f"Here's a hint: {hints[0]}!",
            colour=Colours.pink
        )

        await ctx.send(embed=h_embed)
        await asyncio.sleep(TIMELIMIT)

        h_embed = discord.Embed(
            title=f"Here's a hint: {hints[1]}!",
            colour=Colours.pink
        )
        
        await ctx.send(embed=h_embed)
        await asyncio.sleep(TIMELIMIT)

        if self.winner != " ":
            content = "Well done " + self.winner + " for getting it correct!"
        else:
            content = "Nobody got it right..."

        a_embed = discord.Embed(
            title=f"The answer is: {self.correct}!",
            colour=Colours.pink
        )

        await ctx.send(content, embed=a_embed)

        self.winner = " "

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content.lower() == self.correct.lower():
            self.winner = message.author.mention



def setup(bot):
    """Cog load."""

    bot.add_cog(EasterRiddle(bot))
    log.info("Easter Riddle bot loaded")

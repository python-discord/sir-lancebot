import random
from json import loads
from pathlib import Path

import discord
from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES

log = get_logger(__name__)

RIDDLE_QUESTIONS = loads(Path("bot/resources/holidays/easter/easter_riddle.json").read_text("utf8"))

TIMELIMIT = 10


class EasterRiddle(commands.Cog):
    """The Easter quiz cog."""

    def __init__(self, bot: Bot):
        self.bot = bot
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
                    colour=discord.Colour.red(),
                )
            )
            return

        self.current_channel = ctx.channel

        random_question = random.choice(RIDDLE_QUESTIONS)
        question = random_question["question"]
        hints = random_question["riddles"]
        correct = random_question["correct_answer"]

        description = f"You have {TIMELIMIT} seconds before the first hint."

        riddle_embed = discord.Embed(title=question, description=description, colour=Colours.pink)

        await ctx.send(embed=riddle_embed)
        hint_number = 0
        winner = None
        while hint_number < 3:
            try:
                response = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.channel == ctx.channel
                    and m.author != self.bot.user
                    and m.content.lower() == correct.lower(),
                    timeout=TIMELIMIT,
                )
                if response.content.lower() == correct.lower():
                    winner = response.author.mention
                    break
            except TimeoutError:
                hint_number += 1

                try:
                    hint_embed = discord.Embed(
                        title=f"Here's a hint: {hints[hint_number-1]}!",
                        colour=Colours.pink,
                    )
                except IndexError:
                    break
                await ctx.send(embed=hint_embed)

        if winner:
            content = f"Well done {winner} for getting it right!"
        else:
            content = "Nobody got it right..."

        answer_embed = discord.Embed(title=f"The answer is: {correct}!", colour=Colours.pink)

        await ctx.send(content, embed=answer_embed)
        self.current_channel = None


async def setup(bot: Bot) -> None:
    """Easter Riddle Cog load."""
    await bot.add_cog(EasterRiddle(bot))

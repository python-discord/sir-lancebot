import asyncio
import logging
import random
from json import loads
from pathlib import Path
from typing import Union

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

log = logging.getLogger(__name__)

EGGHEAD_QUESTIONS = loads(Path("bot/resources/holidays/easter/egghead_questions.json").read_text("utf8"))


EMOJIS = [
    "\U0001f1e6", "\U0001f1e7", "\U0001f1e8", "\U0001f1e9", "\U0001f1ea",
    "\U0001f1eb", "\U0001f1ec", "\U0001f1ed", "\U0001f1ee", "\U0001f1ef",
    "\U0001f1f0", "\U0001f1f1", "\U0001f1f2", "\U0001f1f3", "\U0001f1f4",
    "\U0001f1f5", "\U0001f1f6", "\U0001f1f7", "\U0001f1f8", "\U0001f1f9",
    "\U0001f1fa", "\U0001f1fb", "\U0001f1fc", "\U0001f1fd", "\U0001f1fe",
    "\U0001f1ff"
]  # Regional Indicators A-Z (used for voting)

TIMELIMIT = 30


class EggheadQuiz(commands.Cog):
    """This cog contains the command for the Easter quiz!"""

    def __init__(self):
        self.quiz_messages = {}

    @commands.command(aliases=("eggheadquiz", "easterquiz"))
    async def eggquiz(self, ctx: commands.Context) -> None:
        """
        Gives a random quiz question, waits 30 seconds and then outputs the answer.

        Also informs of the percentages and votes of each option
        """
        random_question = random.choice(EGGHEAD_QUESTIONS)
        question, answers = random_question["question"], random_question["answers"]
        answers = [(EMOJIS[i], a) for i, a in enumerate(answers)]
        correct = EMOJIS[random_question["correct_answer"]]

        valid_emojis = [emoji for emoji, _ in answers]

        description = f"You have {TIMELIMIT} seconds to vote.\n\n"
        description += "\n".join([f"{emoji} -> **{answer}**" for emoji, answer in answers])

        q_embed = discord.Embed(title=question, description=description, colour=Colours.pink)

        msg = await ctx.send(embed=q_embed)
        for emoji in valid_emojis:
            await msg.add_reaction(emoji)

        self.quiz_messages[msg.id] = valid_emojis

        await asyncio.sleep(TIMELIMIT)

        del self.quiz_messages[msg.id]

        msg = await ctx.fetch_message(msg.id)  # Refreshes message

        total_no = sum([len(await r.users().flatten()) for r in msg.reactions]) - len(valid_emojis)  # - bot's reactions

        if total_no == 0:
            return await msg.delete()  # To avoid ZeroDivisionError if nobody reacts

        results = ["**VOTES:**"]
        for emoji, _ in answers:
            num = [len(await r.users().flatten()) for r in msg.reactions if str(r.emoji) == emoji][0] - 1
            percent = round(100 * num / total_no)
            s = "" if num == 1 else "s"
            string = f"{emoji} - {num} vote{s} ({percent}%)"
            results.append(string)

        mentions = " ".join([
            u.mention for u in [
                await r.users().flatten() for r in msg.reactions if str(r.emoji) == correct
            ][0] if not u.bot
        ])

        content = f"Well done {mentions} for getting it correct!" if mentions else "Nobody got it right..."

        a_embed = discord.Embed(
            title=f"The correct answer was {correct}!",
            description="\n".join(results),
            colour=Colours.pink
        )

        await ctx.send(content, embed=a_embed)

    @staticmethod
    async def already_reacted(message: discord.Message, user: Union[discord.Member, discord.User]) -> bool:
        """Returns whether a given user has reacted more than once to a given message."""
        users = [u.id for reaction in [await r.users().flatten() for r in message.reactions] for u in reaction]
        return users.count(user.id) > 1  # Old reaction plus new reaction

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]) -> None:
        """Listener to listen specifically for reactions of quiz messages."""
        if user.bot:
            return
        if reaction.message.id not in self.quiz_messages:
            return
        if str(reaction.emoji) not in self.quiz_messages[reaction.message.id]:
            return await reaction.message.remove_reaction(reaction, user)
        if await self.already_reacted(reaction.message, user):
            return await reaction.message.remove_reaction(reaction, user)


async def setup(bot: Bot) -> None:
    """Load the Egghead Quiz Cog."""
    await bot.add_cog(EggheadQuiz())

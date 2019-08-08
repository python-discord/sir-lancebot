import asyncio
import logging
import random
from json import load
from pathlib import Path

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class TriviaQuiz(commands.Cog):
    """A cog for all quiz commands."""

    def __init__(self, bot):
        self.bot = bot
        self.questions = self.load_questions()
        self.games = []
        self.channels = []  # Channels in which the quiz is running.
        # self.done_questions = []
        # self.scoreboard = {
        #     "players": [],
        #     "points": []
        # }

    @staticmethod
    def load_questions():
        p = Path("bot", "resources", "evergreen", "trivia_quiz.json ")
        with p.open() as json_data:
            questions = load(json_data)
            return questions

    @commands.group(name="tquiz", invoke_without_commands=True)
    async def tquiz(self, ctx):
        pass

    @tquiz.command(name="start")
    async def start(self, ctx):
        """start a guiz!"""

        index = self.get_index(ctx.channel.id)
        if index is None:
            return await ctx.send("")
        if ctx.author.id in self.games[]:
            pass


    @tquiz.command(name="start")
    async def start_quiz(self, ctx):
        """start the quiz."""

        index = self.get_index(ctx.author.id)
        if index is None:
            return await ctx.send("You must setup a game first in order to start/play it.")
        self.game_data["games"][index][3] = True
        channel = self.game_data["games"][index][2]
        embed = discord.Embed(colour=discord.Colour.blue())
        embed.title = "Game starting with the following players: "
        embed.description = ""
        for player_id in self.game_data["players"][index]:
            guild = ctx.guild
            player = guild.get_member(player_id)
            embed.description += f"- {player}"
        await ctx.send(embed=embed)
        await asyncio.sleep(2)
        await self.send_question(channel, index)

    async def send_question(self, channel, index):
        """This function is to be called whenever a question needs to be sent."""

        embed = discord.Embed(colour=discord.Colour.dark_gold())
        qtype = "climate"
        q_category = self.questions[qtype]
        q_data = random.choice(q_category)

        self.game_data["done_questions"][index].append(q_data["id"])
        question = q_data["question"]
        no_done_q = len(self.game_data["done_questions"][index])
        embed.title = f"Question #{no_done_q}"
        embed.description = question
        message = await channel.send(embed=embed)
        self.game_data["games"][index].append(message)

        if q_data["type"] == "True_or_False":
            t_emoji = "\U0001F1F9"
            f_emoji = "\U0001F1EB"
            await message.add_reaction(t_emoji)
            await message.add_reaction(f_emoji)

    async def send_hint(self):
        """Function to be called whenever a hint has to be sent."""
        pass

    async def send_response(self):
        """Send response to user when he tries to answer."""
        pass

    @tquiz.command(name="score")
    async def show_score(self, ctx):
        """Show score of each player in the quiz."""

    @tquiz.command(name="stop")
    async def stop_quiz(self, ctx):
        """Stops the quiz"""
        pass


def setup(bot):
    """Loading the cog."""
    bot.add_cog(TriviaQuiz(bot))
    logger.debug("TriviaQuiz cog loaded!")

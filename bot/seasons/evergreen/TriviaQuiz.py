import asyncio
import logging
import random
from dataclasses import dataclass
from json import load
from pathlib import Path

from fuzzywuzzy import fuzz

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


@dataclass
class GameData:
    """TODO documentation"""
    owner: int
    players = []
    points = []
    done_questions = []
    category: str
    question: dict = None
    hints = 0


class TriviaQuiz(commands.Cog):
    """A cog for all quiz commands."""

    def __init__(self, bot):
        self.bot = bot
        self.questions = self.load_questions()
        self.games = {}  # channel as key and value as instinct of dataclass GameData
        self.categories = {
            # "mixed": "Questions from all categories",
            "climate": "Questions related to climate change.",
        }

    @staticmethod
    def load_questions():
        p = Path("bot", "resources", "evergreen", "trivia_quiz.json ")
        with p.open() as json_data:
            questions = load(json_data)
            return questions

    @commands.group(name="tquiz", invoke_without_command=False)
    async def tquiz(self, ctx):
        pass
        # embed = self.category_embed()
        # await ctx.send(embed=embed)

    @tquiz.command(name="start")
    async def start(self, ctx, category=None):
        """start a guiz!"""
        if ctx.channel.id in list(self.games.keys()):
            return await ctx.send("Game already running in this channel!")

        if category is None:
            category = random.choice(list(self.categories.keys()))

        else:
            category = category.lower()
            if category not in self.categories.keys():
                embed = self.category_embed()
                return await ctx.send(f"Category {category} does not exist!", embed=embed)

        self.games[ctx.channel.id] = GameData(
            owner=ctx.author.id,
            category=category
        )

        await self.send_question(ctx.channel)

    def category_embed(self):
        embed = discord.Embed(colour=discord.Colour.blue())
        embed.title = "The available question categories are:"
        embed.description = ""
        for cat, description in self.categories.items():
            embed.description += f"**- {cat.capitalize()}**\n{description.capitalize()}\n"
        embed.set_footer(text="If not category is chosen, then a random one will be selected.")
        return embed

    async def send_question(self, channel):
        """This function is to be called whenever a question needs to be sent."""
        game = self.games[channel.id]
        category = game.category
        category_dict = self.questions[category]
        question_dict = random.choice(category_dict)

        same_question = True
        while same_question is True:
            question_dict = random.choice(category_dict)
            if question_dict["id"] not in game.done_questions:
                same_question = False
            else:
                pass

        question_dict["points"] = 100
        game.question = question_dict
        game.hints = 0

        embed = discord.Embed(colour=discord.Colour.dark_gold())

        question = question_dict["question"]
        question_id = question_dict["id"]

        game.done_questions.append(question_id)
        question_number = len(game.done_questions)

        embed.title = f"#{question_number} Question"
        embed.description = question
        embed.set_footer(text="A hint will be provided after every 10s if no one gives the right answer.Max of 2 hints")

        await channel.send(embed=embed)
        await self.send_hint(channel, question_dict)

    @commands.Cog.listener()
    async def on_message(self, message):

        channel = message.channel
        if channel.id not in list(self.games.keys()):
            pass
        else:
            if message.author.bot:
                pass

            game = self.games[message.channel.id]
            question_data = game.question
            points = question_data["points"]
            answer = question_data["answer"].lower()
            user_answer = message.content.lower()
            ratio = fuzz.ratio(answer, user_answer)
            if ratio > 84:
                if message.author in game.players:
                    author_index = game.players.index(message.author)
                    game.points[author_index] = game.points[author_index] + points
                else:
                    game.players.append(message.author)
                    game.points.append(points)

                await channel.send(f"{message.author.mention} got it right! Good job :tada:"
                                   f"You got {points} points.")
                await self.score_embed(channel)
                await self.send_question(channel)

    async def send_hint(self, channel, question_dict):
        """Function to be called whenever a hint has to be sent."""
        await asyncio.sleep(10)
        game = self.games[channel.id]
        print(f"QD: {question_dict}")
        print(f"GD: {game.question}")

        if question_dict["id"] == game.question["id"]:
            if 2 - game.hints == 0:
                return await self.send_answer(channel)
            hint_list = question_dict["hints"]
            hint_index = game.hints
            hint = hint_list[hint_index]
            game.hints += 1
            embed = discord.Embed(colour=discord.Colour.blue())
            embed.title = f"Hint No.{game.hints}"
            embed.description = hint
            embed.set_footer(text=f"Number of hints remaining: {2-game.hints}")
            await channel.send(embed=embed)
            await self.send_hint(channel, question_dict)
        else:
            await channel.send("no hint")

    async def send_answer(self, channel):
        """A function to send the answer in the channel if no user have given the correct answer even after 2 hints."""
        game = self.games[channel.id]
        answer = game.question["answer"]
        await channel.send(f"All of you failed, the correct answer is {answer}.")
        await self.score_embed(channel)
        await self.send_question(channel)

    @tquiz.command(name="score")
    async def send_score(self, ctx):
        await self.score_embed(ctx.channel)

    async def score_embed(self, channel):
        """Show score of each player in the quiz."""
        if channel.id not in list(self.games.keys()):
            return await channel.send("There are no games running in this channel!")
        game = self.games[channel.id]
        players = game.players
        points = game.points
        embed = discord.Embed(color=discord.Colour.dark_gold())
        embed.title = "Scoreboard"
        embed.description = ""
        for player, score in zip(players, points):
            embed.description = f"{player} - {score}\n"
        await channel.send(embed=embed)

    @tquiz.command(name="stop")
    async def stop_quiz(self, ctx):
        """Stop the quiz."""
        await ctx.send("Game is not running anymore!")
        await self.score_embed(ctx.channel)
        await asyncio.sleep(2)
        del self.games[ctx.channel.id]


def setup(bot):
    """Loading the cog."""
    bot.add_cog(TriviaQuiz(bot))
    logger.debug("TriviaQuiz cog loaded!")

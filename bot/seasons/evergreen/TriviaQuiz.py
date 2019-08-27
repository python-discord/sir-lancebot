import asyncio
import logging
import random
from dataclasses import dataclass
from json import load
from pathlib import Path

import discord
from discord.ext import commands
from fuzzywuzzy import fuzz

from bot.constants import Roles


logger = logging.getLogger(__name__)


annoyed_expressions = ["-_-", "-.-"]

wrong_ans_responses = [
    "No one gave the correct answer",
    "Losers",
    "You guys really need to learn"
]


@dataclass
class GameData:
    """A dataclass for game data."""

    owner: int
    players = []
    points = []
    done_questions = []
    category: str
    question: dict = None
    hints = 0
    unanswered_questions = 0


class TriviaQuiz(commands.Cog):
    """A cog for all quiz commands."""

    def __init__(self, bot):
        self.bot = bot
        self.questions = self.load_questions()
        self.games = {}  # channel as key and value as instinct of dataclass GameData
        self.categories = {
            "retro": "Questions related to retro gaming."
        }
        self.inactivity_limit = 3  # Number of questions unanswered in a row after which quiz stops.

    @staticmethod
    def load_questions():
        """Load the questions from  json file."""
        p = Path("bot", "resources", "evergreen", "trivia_quiz.json ")
        with p.open() as json_data:
            questions = load(json_data)
            return questions

    @commands.group(name="tquiz", invoke_without_command=False)
    async def tquiz(self, ctx):
        """Trivia Quiz game for fun!"""
        await ctx.send_help("tquiz")

    @tquiz.command(name="start")
    async def start(self, ctx, category=None):
        """Start a quiz!

        Questions for the quiz can be selected from the following categories:
        - Retro : questions related to retro gaming.
        """
        await ctx.send("Quiz triggered! Gonna start in a couple of seconds...")
        await asyncio.sleep(1)

        # Checking if there is already a game running in that channel.
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
        """A function which returns an embed showing all avilable categories"""
        embed = discord.Embed(colour=discord.Colour.blue())
        embed.title = "The available question categories are:"
        embed.description = ""
        for cat, description in self.categories.items():
            embed.description += f"**- {cat.capitalize()}**\n{description.capitalize()}\n"
        embed.set_footer(text="If not category is chosen, then a random one will be selected.")
        return embed

    async def send_question(self, channel):
        """This function is to be called whenever a question needs to be sent."""
        await asyncio.sleep(2)
        game = self.games[channel.id]
        if game.unanswered_questions == self.inactivity_limit:
            del self.games[channel.id]
            return await channel.send("Game stopped due to inactivity.")

        category = game.category
        category_dict = self.questions[category]
        question_dict = random.choice(category_dict)

        same_question = True

        # Making sure a question is not repeated.
        while same_question is True:
            question_dict = random.choice(category_dict)
            if question_dict["id"] not in game.done_questions:
                same_question = False
            else:
                pass

        # Initial points for a question.
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
        """A function triggered when a message is sent."""
        channel = message.channel
        if channel.id not in list(self.games.keys()):
            return
        if message.author.bot:
            return

        game = self.games[message.channel.id]
        question_data = game.question
        answer = question_data["answer"].lower()
        user_answer = message.content.lower()
        ratio = fuzz.ratio(answer, user_answer)
        if ratio > 84:
            points = question_data["points"] - game.hints*25
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
        elif ratio in range(75, 84):
            await channel.send(f"Your close to the answer {message.author.mention}")

    async def send_hint(self, channel, question_dict):
        """Function to be called whenever a hint has to be sent."""
        await asyncio.sleep(10)
        try:
            game = self.games[channel.id]
        except KeyError:
            return

        # Checking if the question is the same after 10 seconds.
        if question_dict["id"] == game.question["id"]:

            # If the max number of hints is already reached, then send the answer.
            if 2 - game.hints == 0:
                return await self.send_answer(channel)

            hint_list = question_dict["hints"]
            hint_index = game.hints
            hint = hint_list[hint_index]
            game.hints += 1
            message = f"**Hint {game.hints}**: {hint}\n*Number of hints remaining: {2-game.hints}*"
            await channel.send(message)
            await self.send_hint(channel, question_dict)
        else:
            pass

    async def send_answer(self, channel):
        """A function to send the answer in the channel if no user have given the correct answer even after 2 hints."""
        game = self.games[channel.id]
        answer = game.question["answer"]
        response = random.choice(wrong_ans_responses)
        expression = random.choice(annoyed_expressions)
        await channel.send(f"{response} {expression}, the correct answer is **{answer}**.")
        self.games[channel.id].unanswered_questions += 1
        await self.score_embed(channel)
        await self.send_question(channel)

    @tquiz.command(name="score")
    async def send_score(self, ctx):
        """Show scoreboard of the game running in this channel."""
        await self.score_embed(ctx.channel)

    async def score_embed(self, channel):
        """Show score of each player in the quiz."""
        if channel.id not in list(self.games.keys()):
            return await channel.send("There are no games running in this channel!")
        game = self.games[channel.id]
        players = game.players
        if len(players) == 0:
            return
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
        if ctx.channel.id not in list(self.games.keys()):
            return await ctx.send("No game running, nothing to stop here -.-")
        game = self.games[ctx.channel.id]
        owner = game.owner
        mods = Roles.moderator
        if ctx.author.id == owner or mods in [role.id for role in ctx.author.roles]:
            await ctx.send("Game is not running anymore!")
            await self.score_embed(ctx.channel)
            if game.players:
                highest_points = max(game.points)
                author_index = game.points.index(highest_points)
                winner = game.players[author_index]
                await ctx.send(
                    f"Congratz {winner.mention} :tada: "
                    f"You have won this quiz game with a grand total of {highest_points} points!!"
                )
            await asyncio.sleep(2)
            del self.games[ctx.channel.id]
        else:
            await ctx.send("You are not authorised to close this game!")


def setup(bot):
    """Loading the cog."""
    bot.add_cog(TriviaQuiz(bot))
    logger.debug("TriviaQuiz cog loaded!")

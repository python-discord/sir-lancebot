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
        self.question_dicts = []
        self.categories = {
            "mixed": "Questions from all categories",
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
        if ctx.channel.id in self.channels:
            return await ctx.send("Game already running in this channel!")

        if category is None:
            category = random.choice(list(self.categories.keys()))

        else:
            category = category.lower()
            if category not in self.categories.keys():
                embed = self.category_embed()
                return await ctx.send(f"Category {category} does not exist!", embed=embed)

        self.channels.append(ctx.channel.id)
        self.question_dicts.append(0)

        game_dict = {
            "owner": ctx.author.id,
            "players": [],
            "points": [],
            "done_questions": [],
            "category": category
        }
        self.games.append(game_dict)

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
        # task = asyncio.create_task(self.send_hint(channel))
        game_index = self.channels.index(channel.id)
        category = self.games[game_index]["category"]
        self.games[game_index]["hint_index"] = 0
        category_dict = self.questions[category]
        question_dict = random.choice(category_dict)

        same_question = True
        while same_question is True:
            question_dict = random.choice(category_dict)
            if question_dict["id"] not in self.games[game_index]["done_questions"]:
                same_question = False
            else:
                pass

        question_dict["points"] = 100
        self.question_dicts[game_index] = question_dict

        embed = discord.Embed(colour=discord.Colour.dark_gold())

        question = question_dict["question"]
        question_id = question_dict["id"]
        answer = question_dict["answer"]

        self.games[game_index]["done_questions"].append(question_id)
        question_number = len(self.games[game_index]["done_questions"])

        embed.title = f"#{question_number} Question"
        embed.description = question
        embed.set_footer(text="A hint will be provided after every 10s if no one gives the right answer.Max of 2 hints")

        await channel.send(embed=embed)
        # await task

    @commands.Cog.listener()
    async def on_message(self, message):

        channel = message.channel
        if channel.id not in self.channels:
            pass

        else:
            if message.author.bot:
                pass

            game_index = self.channels.index(channel.id)
            game = self.games[game_index]
            question_data = self.question_dicts[game_index]
            points = question_data["points"]
            if message.content.lower() == question_data["answer"].lower():
                if message.author in game["players"]:
                    author_index = game["players"].index(message.author)
                    game["points"][author_index] = game["points"][author_index] + points
                else:
                    game["players"].append(message.author)
                    game["points"].append(points)

                await channel.send(f"{message.author.mention} got it right! Good job :tada:"
                                   f"You got {points} points.")
                await asyncio.sleep(2)
                await self.score_embed(channel)
                await self.send_question(channel)

    async def send_hint(self, channel):
        """Function to be called whenever a hint has to be sent."""
        await asyncio.sleep(10)
        game_index = self.channels.index(channel.id)
        self.question_dicts[game_index]["points"] -= 25
        hints = self.question_dicts[game_index]["hints"]
        hint_index = self.games[game_index]["hint_index"]
        self.games[game_index]["hint_index"] += 1
        hint = hints[hint_index]
        embed = discord.Embed(colour=discord.Colour.blue())
        embed.title = f"Hint #{hint_index + 1}"
        embed.description = hint
        embed.set_footer(text=f"Remaining hints: {1 - hint_index}.")
        await channel.send(embed=embed)

    @tquiz.command(name="score")
    async def send_score(self, ctx):
        await self.score_embed(ctx.channel)

    async def score_embed(self, channel):
        """Show score of each player in the quiz."""
        if channel.id not in self.channels:
            return await channel.send("There are no games running in this channel!")
        game_index = self.channels.index(channel.id)
        game = self.games[game_index]
        players = game["players"]
        points = game["points"]
        embed = discord.Embed(color=discord.Colour.dark_gold())
        embed.title = "Scoreboard"
        embed.description = "```\n"
        for player, score in zip(players, points):
            embed.description = f"{player} - {score}\n"
        await channel.send(embed=embed)

    @tquiz.command(name="stop")
    async def stop_quiz(self, ctx):
        """Stops the quiz"""
        pass


def setup(bot):
    """Loading the cog."""
    bot.add_cog(TriviaQuiz(bot))
    logger.debug("TriviaQuiz cog loaded!")

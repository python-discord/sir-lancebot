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

        category = category.lower()

        if category not in self.categories.keys():
            embed = self.category_embed()
            return await ctx.send(f"Category {category} does not exist!", embed=embed)

        if category is None:
            category = random.choice(self.categories)

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
        game_index = self.channels.index(channel.id)
        category = self.games[game_index]["category"]
        category_dict = self.questions[category]
        question_dict = random.choice(category_dict)

        same_question = True
        while same_question is True:
            question_dict = random.choice(category_dict)
            if question_dict["id"] not in self.games[game_index]["done_questions"]:
                same_question = False
            else:
                pass

        self.question_dicts[game_index] = question_dict

        embed = discord.Embed(colour=discord.Colour.dark_gold())

        question = question_dict["question"]
        question_id = question_dict["id"]
        answer = question_dict["answer"]

        self.games[game_index]["done_questions"].append(question_id)
        question_number = len(self.games[game_index]["done_questions"])

        embed.title = f"#{question_number} Question"
        embed.description = question

        await channel.send(embed=embed)

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
            if message.content.lower() == question_data["answer"].lower():
                if message.author in game["players"]:
                    author_index = game["players"].index(message.author)
                    game["points"][author_index] = game["points"][author_index] + 100
                else:
                    game["players"].append(message.author)
                    game["points"].append(100)

                await channel.send(f"{message.author.mention} got it right! Good job :tada:")
                await asyncio.sleep(2)
                await self.send_question(channel)

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

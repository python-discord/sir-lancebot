import logging
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
        self.game_data = {
            "games": [],
            "players": [],
            "points": []
        }

    @staticmethod
    def load_questions():
        p = Path("bot", "resources", "evergreen", "trivia_quiz.json ")
        with p.open() as json_data:
            questions = load(json_data)
            return questions

    @commands.group(name="tquiz", invoke_without_commands=True)
    async def tquiz(self, ctx):
        pass

    @tquiz.command(name="invite")
    async def join(self, ctx, quiz_id):
        """Join a quiz game."""
        pass

    @tquiz.command(name="start")
    async def start_quiz(self, ctx):
        """Start the quiz!"""

        for player_list in self.game_data["players"]:
            if ctx.author.id in player_list:
                return await ctx.send("You are already in a game!")

        game_id = "abc"  # should be randomly generated id

        started = False
        new_game = [ctx.author.id, game_id, ctx.channel.id, started]

        self.game_data["games"].append(new_game)
        self.game_data["players"].append([ctx.author.id])
        self.game_data["points"].append([0])

        print(self.game_data)
        await self.send_question(ctx.channel)

    async def send_question(self, channel):
        """This function is to be called whenever a question needs to be sent."""

        embed = discord.Embed(colour=discord.Colour.dark_gold())
        await channel.send("here is the question.")

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

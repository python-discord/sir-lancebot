import asyncio
import json
import logging
import random
from pathlib import Path

import discord
from discord.ext import commands
from fuzzywuzzy import fuzz

from bot.constants import Roles


logger = logging.getLogger(__name__)


ANNOYED_EXPRESSIONS = ["-_-", "-.-"]

WRONG_ANS_RESPONSE = [
    "No one gave the correct answer",
    "Better luck next time"
]


class TriviaQuiz(commands.Cog):
    """A cog for all quiz commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.questions = self.load_questions()
        self.game_status = {}
        self.game_owners = {}
        self.question_limit = 3
        self.categories = {
            "general": "Test your general knwoledge",
            "retro": "Questions related to retro gaming."
        }

    @staticmethod
    def load_questions() -> dict:
        """Load the questions from  json file."""
        p = Path("bot", "resources", "evergreen", "trivia_quiz.json")
        with p.open() as json_data:
            questions = json.load(json_data)
            return questions

    @commands.command(name="quiz")
    async def start(self, ctx: commands.Context, option: str, category: str = "general") -> None:
        """
        Start/Stop a quiz!

        arguments:
        option:
        - start : to start a quiz in a channel
        - stop  : stop the quiz running in that channel.

        Questions for the quiz can be selected from the following categories:
        - general : Test your general knowledge. (default)
        - Retro : questions related to retro gaming.
        """
        category = category.lower()
        player_data = {}  # a dict to store players and their points.

        if ctx.channel.id not in self.game_status:
            self.game_status[ctx.channel.id] = None

        if option == "start":
            if self.game_status[ctx.channel.id] is True:
                await ctx.send("Game already running.")
                return
            else:
                self.game_owners[ctx.channel.id] = ctx.author
                self.game_status[ctx.channel.id] = True
                start_embed = discord.Embed(colour=discord.Colour.red())
                start_embed.title = "Quiz game Starting!!"
                start_embed.description = "Each game consists of 5 questions.\n"
                start_embed.description += "**Rules :**\nNo cheating and have fun!"
                start_embed.set_footer(text="2 hints per question sent after every 10s")
                await ctx.send(embed=start_embed)  # send an embed with the rules

        elif option == "stop":
            if self.game_status[ctx.channel.id] is False:
                await ctx.send("No game running, nothing to stop here.")
                return
            else:
                if (
                        ctx.author == self.game_owners[ctx.channel.id]
                        or Roles.moderator in [role.id for role in ctx.author.roles]
                ):
                    await self.declare_winner(ctx.channel, player_data)
                    self.game_status[ctx.channel.id] = False
                    del self.game_owners[ctx.channel.id]
                else:
                    await ctx.send(f"{ctx.author.mention}, you are not authorised to stop this game :ghost: !")

        if category not in self.categories:
            embed = self.category_embed
            await ctx.send(embed=embed)
            return
        topic = self.questions[category]

        unanswered = 0
        done_question = []
        hint_no = 0
        answer = None
        hints = None
        while self.game_status[ctx.channel.id] is True:
            if len(done_question) > self.question_limit and hint_no == 0:
                await ctx.send("The round ends here.")
                await self.declare_winner(ctx.channel, player_data)
                break
            if unanswered > 3:
                await ctx.send("Game stopped due to inactivity.")
                await self.declare_winner(ctx.channel, player_data)
                break
            if hint_no == 0:
                while True:
                    question_dict = random.choice(topic)
                    if question_dict["id"] not in done_question:
                        done_question.append(question_dict["id"])
                        break
                q = question_dict["question"]
                answer = question_dict["answer"]
                hints = question_dict["hints"]

                embed = discord.Embed(colour=discord.Colour.gold())
                embed.title = f"Question #{len(done_question)}"
                embed.description = q
                await ctx.send(embed=embed)

            def check(m):
                ratio = fuzz.ratio(answer.lower(), m.content)
                return ratio > 80 and m.channel == ctx.channel
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=10)
            except Exception as e:
                if self.game_status[ctx.channel.id] is False:
                    break
                if isinstance(e, asyncio.TimeoutError):
                    if hint_no < 2:
                        await ctx.send(f"**Hint #{hint_no+1}\n**{hints[hint_no]}")
                        hint_no += 1
                    else:
                        response = random.choice(WRONG_ANS_RESPONSE)
                        expression = random.choice(ANNOYED_EXPRESSIONS)
                        await ctx.send(f"{response} {expression}, the correct answer is **{answer}**.")
                        hint_no = 0
                        unanswered += 1
                        await self.send_score(ctx.channel, player_data)

            else:
                points = 100 - 25*hint_no
                if msg.author in player_data:
                    player_data[msg.author] += points
                else:
                    player_data[msg.author] = points
                hint_no = 0
                unanswered = 0
                await ctx.send(f"{msg.author.mention} got the correct answer :tada: {points} points for ya.")
                await ctx.send(f"Correct answer is **{answer}**")
                await self.send_score(ctx.channel, player_data)

    @staticmethod
    async def send_score(channel: discord.TextChannel, player_data: dict) -> None:
        """A function which sends the score."""
        embed = discord.Embed(colour=discord.Colour.blue())
        embed.title = "Score Board"
        embed.description = ""
        for k, v in player_data.items():
            embed.description += f"{k} : {v}\n"
        await channel.send(embed=embed)

    @staticmethod
    async def declare_winner(channel: discord.TextChannel, player_data: dict) -> None:
        """A function declare the winner of the quiz."""
        if player_data:
            highest_points = max(list(player_data.values()))
            no_of_winners = list(player_data.values()).count(highest_points)

            # Check if more than 1 player has highest points.
            if no_of_winners > 1:
                winners = []
                points_copy = list(player_data.values()).copy()
                for _ in range(no_of_winners):
                    index = points_copy.index(highest_points)
                    winners.append(list(player_data.keys())[index])
                    points_copy[index] = 0
                winners_mention = None
                for winner in winners:
                    winners_mention += f"{winner.mention} "

            else:
                author_index = list(player_data.values()).index(highest_points)
                winner = list(player_data.keys())[author_index]
                winners_mention = winner.mention
            await channel.send(
                f"Congratz {winners_mention} :tada: "
                f"You have won this quiz game with a grand total of {highest_points} points!!"
            )

    @property
    def category_embed(self) -> discord.Embed:
        """A function which returns an embed showing all avilable categories."""
        embed = discord.Embed(colour=discord.Colour.blue())
        embed.title = "The available question categories are:"
        embed.description = ""
        for cat, description in self.categories.items():
            embed.description += f"**- {cat.capitalize()}**\n{description.capitalize()}\n"
        embed.set_footer(text="If not category is chosen, then a random one will be selected.")
        return embed


def setup(bot: commands.Bot) -> None:
    """Loading the cog."""
    bot.add_cog(TriviaQuiz(bot))
    logger.debug("TriviaQuiz cog loaded!")

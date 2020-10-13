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


WRONG_ANS_RESPONSE = [
    "No one answered correctly!",
    "Better luck next time"
]


class TriviaQuiz(commands.Cog):
    """A cog for all quiz commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.questions = self.load_questions()
        self.game_status = {}  # A variable to store the game status: either running or not running.
        self.game_owners = {}  # A variable to store the person's ID who started the quiz game in a channel.
        self.question_limit = 4
        self.player_scores = {}  # A variable to store all player's scores for a bot session.
        self.game_player_scores = {}  # A variable to store temporary game player's scores.
        self.categories = {
            "general": "Test your general knowledge"
            # "retro": "Questions related to retro gaming."
        }

    @staticmethod
    def load_questions() -> dict:
        """Load the questions from the JSON file."""
        p = Path("bot", "resources", "evergreen", "trivia_quiz.json")
        with p.open(encoding="utf8") as json_data:
            questions = json.load(json_data)
            return questions

    @commands.group(name="quiz", aliases=["trivia"], invoke_without_command=True)
    async def quiz_game(self, ctx: commands.Context, category: str = None) -> None:
        """
        Start a quiz!

        Questions for the quiz can be selected from the following categories:
        - general : Test your general knowledge. (default)
        (More to come!)
        """
        if ctx.channel.id not in self.game_status:
            self.game_status[ctx.channel.id] = False

        if ctx.channel.id not in self.game_player_scores:
            self.game_player_scores[ctx.channel.id] = {}

        # Stop game if running.
        if self.game_status[ctx.channel.id] is True:
            return await ctx.send(
                f"Game is already running..."
                f"do `{self.bot.command_prefix}quiz stop`"
            )

        # Send embed showing available categories if inputted category is invalid.
        if category is None:
            category = random.choice(list(self.categories))

        category = category.lower()
        if category not in self.categories:
            embed = self.category_embed()
            await ctx.send(embed=embed)
            return

        # Start game if not running.
        if self.game_status[ctx.channel.id] is False:
            self.game_owners[ctx.channel.id] = ctx.author
            self.game_status[ctx.channel.id] = True
            start_embed = self.make_start_embed(category)

            await ctx.send(embed=start_embed)  # send an embed with the rules
            await asyncio.sleep(1)

        topic = self.questions[category]

        done_question = []
        hint_no = 0
        answer = None
        while self.game_status[ctx.channel.id]:
            # Exit quiz if number of questions for a round are already sent.
            if len(done_question) > self.question_limit and hint_no == 0:
                await ctx.send("The round has ended.")
                await self.declare_winner(ctx.channel, self.game_player_scores[ctx.channel.id])

                self.game_status[ctx.channel.id] = False
                del self.game_owners[ctx.channel.id]
                self.game_player_scores[ctx.channel.id] = {}

                break

            # If no hint has been sent or any time alert. Basically if hint_no = 0  means it is a new question.
            if hint_no == 0:
                # Select a random question which has not been used yet.
                while True:
                    question_dict = random.choice(topic)
                    if question_dict["id"] not in done_question:
                        done_question.append(question_dict["id"])
                        break

                q = question_dict["question"]
                answer = question_dict["answer"]

                embed = discord.Embed(colour=discord.Colour.gold())
                embed.title = f"Question #{len(done_question)}"
                embed.description = q
                await ctx.send(embed=embed)  # Send question embed.

            # A function to check whether user input is the correct answer(close to the right answer)
            def check(m: discord.Message) -> bool:
                return (
                    m.channel == ctx.channel
                    and fuzz.ratio(answer.lower(), m.content.lower()) > 85
                )

            try:
                msg = await self.bot.wait_for('message', check=check, timeout=10)
            except asyncio.TimeoutError:
                # In case of TimeoutError and the game has been stopped, then do nothing.
                if self.game_status[ctx.channel.id] is False:
                    break

                # if number of hints sent or time alerts sent is less than 2, then send one.
                if hint_no < 2:
                    hint_no += 1
                    if "hints" in question_dict:
                        hints = question_dict["hints"]
                        await ctx.send(f"**Hint #{hint_no+1}\n**{hints[hint_no]}")
                    else:
                        await ctx.send(f"{30 - hint_no * 10}s left!")

                # Once hint or time alerts has been sent 2 times, the hint_no value will be 3
                # If hint_no > 2, then it means that all hints/time alerts have been sent.
                # Also means that the answer is not yet given and the bot sends the answer and the next question.
                else:
                    if self.game_status[ctx.channel.id] is False:
                        break

                    response = random.choice(WRONG_ANS_RESPONSE)
                    await ctx.send(response)
                    await self.send_answer(ctx.channel, question_dict)
                    await asyncio.sleep(1)

                    hint_no = 0  # init hint_no = 0 so that 2 hints/time alerts can be sent for the new question.

                    await self.send_score(ctx.channel, self.game_player_scores[ctx.channel.id])
                    await asyncio.sleep(2)
            else:
                if self.game_status[ctx.channel.id] is False:
                    break

                # Reduce points by 25 for every hint/time alert that has been sent.
                points = 100 - 25*hint_no
                if msg.author in self.game_player_scores[ctx.channel.id]:
                    self.game_player_scores[ctx.channel.id][msg.author] += points
                else:
                    self.game_player_scores[ctx.channel.id][msg.author] = points

                # Also updating the overall scoreboard.
                if msg.author in self.player_scores:
                    self.player_scores[msg.author] += points
                else:
                    self.player_scores[msg.author] = points

                hint_no = 0

                await ctx.send(f"{msg.author.mention} got the correct answer :tada: {points} points!")
                await self.send_answer(ctx.channel, question_dict)
                await self.send_score(ctx.channel, self.game_player_scores[ctx.channel.id])
                await asyncio.sleep(2)

    @staticmethod
    def make_start_embed(category: str) -> discord.Embed:
        """Generate a starting/introduction embed for the quiz."""
        start_embed = discord.Embed(colour=discord.Colour.red())
        start_embed.title = "Quiz game Starting!!"
        start_embed.description = "Each game consists of 5 questions.\n"
        start_embed.description += "**Rules :**\nNo cheating and have fun!"
        start_embed.description += f"\n **Category** : {category}"
        start_embed.set_footer(
            text="Points for each question reduces by 25 after 10s or after a hint. Total time is 30s per question"
        )
        return start_embed

    @quiz_game.command(name="stop")
    async def stop_quiz(self, ctx: commands.Context) -> None:
        """
        Stop a quiz game if its running in the channel.

        Note: Only mods or the owner of the quiz can stop it.
        """
        if self.game_status[ctx.channel.id] is True:
            # Check if the author is the game starter or a moderator.
            if (
                ctx.author == self.game_owners[ctx.channel.id]
                or any(Roles.moderator == role.id for role in ctx.author.roles)
            ):
                await ctx.send("Quiz stopped.")
                await self.declare_winner(ctx.channel, self.game_player_scores[ctx.channel.id])

                self.game_status[ctx.channel.id] = False
                del self.game_owners[ctx.channel.id]
                self.game_player_scores[ctx.channel.id] = {}
            else:
                await ctx.send(f"{ctx.author.mention}, you are not authorised to stop this game :ghost:!")
        else:
            await ctx.send("No quiz running.")

    @quiz_game.command(name="leaderboard")
    async def leaderboard(self, ctx: commands.Context) -> None:
        """View everyone's score for this bot session."""
        await self.send_score(ctx.channel, self.player_scores)

    @staticmethod
    async def send_score(channel: discord.TextChannel, player_data: dict) -> None:
        """A function which sends the score."""
        if len(player_data) == 0:
            await channel.send("No one has made it onto the leaderboard yet.")
            return

        embed = discord.Embed(colour=discord.Colour.blue())
        embed.title = "Score Board"
        embed.description = ""

        sorted_dict = sorted(player_data.items(), key=lambda a: a[1], reverse=True)
        for item in sorted_dict:
            embed.description += f"{item[0]} : {item[1]}\n"

        await channel.send(embed=embed)

    @staticmethod
    async def declare_winner(channel: discord.TextChannel, player_data: dict) -> None:
        """Announce the winner of the quiz in the game channel."""
        if player_data:
            highest_points = max(list(player_data.values()))
            no_of_winners = list(player_data.values()).count(highest_points)

            # Check if more than 1 player has highest points.
            if no_of_winners > 1:
                word = "You guys"
                winners = []
                points_copy = list(player_data.values()).copy()

                for _ in range(no_of_winners):
                    index = points_copy.index(highest_points)
                    winners.append(list(player_data.keys())[index])
                    points_copy[index] = 0

                winners_mention = " ".join(winner.mention for winner in winners)
            else:
                word = "You"
                author_index = list(player_data.values()).index(highest_points)
                winner = list(player_data.keys())[author_index]
                winners_mention = winner.mention

            await channel.send(
                f"Congratulations {winners_mention} :tada: "
                f"{word} have won this quiz game with a grand total of {highest_points} points!"
            )

    def category_embed(self) -> discord.Embed:
        """Build an embed showing all available trivia categories."""
        embed = discord.Embed(colour=discord.Colour.blue())
        embed.title = "The available question categories are:"
        embed.set_footer(text="If a category is not chosen, a random one will be selected.")
        embed.description = ""

        for cat, description in self.categories.items():
            embed.description += f"**- {cat.capitalize()}**\n{description.capitalize()}\n"

        return embed

    @staticmethod
    async def send_answer(channel: discord.TextChannel, question_dict: dict) -> None:
        """Send the correct answer of a question to the game channel."""
        answer = question_dict["answer"]
        info = question_dict["info"]
        embed = discord.Embed(color=discord.Colour.red())
        embed.title = f"The correct answer is **{answer}**\n"
        embed.description = ""

        if info != "":
            embed.description += f"**Information**\n{info}\n\n"

        embed.description += "Let's move to the next question.\nRemaining questions: "
        await channel.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Load the cog."""
    bot.add_cog(TriviaQuiz(bot))

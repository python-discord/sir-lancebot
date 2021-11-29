import asyncio
from json import JSONDecodeError, loads
from random import choice
from typing import Optional

from discord import Embed
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES, POSITIVE_REPLIES, Roles

from ._questions import QuestionView, Questions
from ._scoreboard import Scoreboard, ScoreboardView

# The ID you see below is the Events Lead role ID
TRIVIA_NIGHT_ROLES = (Roles.admin, 78361735739998228)


class TriviaNight(commands.Cog):
    """Cog for the Python Trivia Night event."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.scoreboard = Scoreboard()
        self.questions = Questions(self.scoreboard)

    def setup_views(self, questions: dict) -> None:
        """
        Sets up the views for `self.questions` and `self.scoreboard` respectively.

        Parameters:
            - questions: The dictionary to set the questions for self.questions to use.
        """
        self.questions.view = QuestionView()
        self.scoreboard.view = ScoreboardView(self.bot)
        self.questions.set_questions(questions)

    @staticmethod
    def unicodeify(text: str) -> str:
        """
        Takes `text` and adds zero-width spaces to prevent copy and pasting the question.

        Parameters:
            - text: A string that represents the question description to 'unicodeify'
        """
        return "".join(
            f"{letter}\u200b" if letter not in ('\n', '\t', '`', 'p', 'y') else letter
            for idx, letter in enumerate(text)
        )

    @commands.group(aliases=["tn"], invoke_without_command=True)
    async def trivianight(self, ctx: commands.Context) -> None:
        """
        The command group for the Python Discord Trivia Night.

        If invoked without a subcommand (i.e. simply .trivianight), it will explain what the Trivia Night event is.
        """
        cog_description = Embed(
            title="What is .trivianight?",
            description=(
                "This 'cog' is for the Python Discord's TriviaNight (date tentative)! Compete against other"
                "players in a trivia about Python!"
            ),
            color=Colours.soft_green
        )
        await ctx.send(embed=cog_description)

    @trivianight.command()
    @commands.has_any_role(*TRIVIA_NIGHT_ROLES)
    async def load(self, ctx: commands.Context, *, to_load: Optional[str]) -> None:
        """
        Loads a JSON file from the provided attachment or argument.

        The JSON provided is formatted where it is a list of dictionaries, each dictionary containing the keys below:
        - number: int (represents the current question #)
        - description: str (represents the question itself)
        - answers: list[str] (represents the different answers possible, must be a length of 4)
        - correct: str (represents the correct answer in terms of what the correct answer is in `answers`
        - time: Optional[int] (represents the timer for the question and how long it should run, default is 10)
        - points: Optional[int] (represents how many points are awarded for each question, default is 10)

        The load command accepts three different ways of loading in a JSON:
        - an attachment of the JSON file
        - a message link to the attachment/JSON
        - reading the JSON itself via a codeblock or plain text
        """
        if ctx.message.attachments:
            json_text = (await ctx.message.attachments[0].read()).decode("utf8")
        elif not to_load:
            raise commands.BadArgument("You didn't attach an attachment nor link a message!")
        elif to_load.startswith("https://discord.com/channels") or \
                to_load.startswith("https://discordapp.com/channels"):
            channel_id, message_id = to_load.split("/")[-2:]
            channel = await ctx.guild.fetch_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))
            if message.attachments:
                json_text = (await message.attachments[0].read()).decode("utf8")
            else:
                json_text = message.content.replace("```", "").replace("json", "").replace("\n", "")
        else:
            json_text = to_load.replace("```", "").replace("json", "").replace("\n", "")

        try:
            serialized_json = loads(json_text)
        except JSONDecodeError:
            raise commands.BadArgument("Invalid JSON")

        for idx, question in enumerate(serialized_json):
            serialized_json[idx]["obfuscated_description"] = self.unicodeify(question["description"])

        self.setup_views(serialized_json)

        success_embed = Embed(
            title=choice(POSITIVE_REPLIES),
            description="The JSON was loaded successfully!",
            color=Colours.soft_green
        )
        await ctx.send(embed=success_embed)

    @trivianight.command()
    @commands.has_any_role(*TRIVIA_NIGHT_ROLES)
    async def reset(self, ctx: commands.Context) -> None:
        """Resets previous questions and scoreboards."""
        all_questions = self.questions.questions

        for question in all_questions:
            if "visited" in question.keys():
                del question["visited"]

        self.setup_views(list(all_questions))

        success_embed = Embed(
            title=choice(POSITIVE_REPLIES),
            description="The scoreboards were reset and questions reset!",
            color=Colours.soft_green
        )
        await ctx.send(embed=success_embed)

    @trivianight.command()
    @commands.has_any_role(*TRIVIA_NIGHT_ROLES)
    async def next(self, ctx: commands.Context) -> None:
        """
        Gets a random question from the unanswered question list and lets the user(s) choose the answer.

        This command will continuously count down until the time limit of the question is exhausted.
        However, if `.trivianight stop` is invoked, the counting down is interrupted to show the final results.
        """
        if self.questions.view.active_question is True:
            error_embed = Embed(
                title=choice(NEGATIVE_REPLIES),
                description="There is already an ongoing question!",
                color=Colours.soft_red
            )
            await ctx.send(embed=error_embed)
            return

        next_question = self.questions.next_question()
        if isinstance(next_question, Embed):
            await ctx.send(embed=next_question)
            return

        (question_embed, time_limit), question_view = self.questions.current_question()
        message = await ctx.send(embed=question_embed, view=question_view)

        for time_remaining in range(time_limit, -1, -1):
            if self.questions.view.active_question is False:
                await ctx.send(embed=self.questions.end_question())
                await message.edit(embed=question_embed, view=None)
                return

            await asyncio.sleep(1)
            if time_remaining % 5 == 0 and time_remaining not in (time_limit, 0):
                await ctx.send(f"{time_remaining}s remaining")

        await ctx.send(embed=self.questions.end_question())
        await message.edit(embed=question_embed, view=None)

    @trivianight.command()
    @commands.has_any_role(*TRIVIA_NIGHT_ROLES)
    async def question(self, ctx: commands.Context, question_number: int) -> None:
        """
        Gets a question from the question bank depending on the question number provided.

        The logic of this command is similar to `.trivianight next`, with the only difference being that you need to
        specify the question number.

        Parameters:
            - question_number: An integer represents the question number to go to (i.e. .trivianight question 5).
        """
        question = self.questions.next_question(question_number)
        if isinstance(question, Embed):
            await ctx.send(embed=question)
            return

        (question_embed, time_limit), question_view = self.questions.current_question()
        message = await ctx.send(embed=question_embed, view=question_view)

        for time_remaining in range(time_limit, -1, -1):
            if self.questions.view.active_question is False:
                await ctx.send(embed=self.questions.end_question())
                await message.edit(embed=question_embed, view=None)
                return

            await asyncio.sleep(1)
            if time_remaining % 5 == 0 and time_remaining not in (time_limit, 0):
                await ctx.send(f"{time_remaining}s remaining")

        await ctx.send(embed=self.questions.end_question())
        await message.edit(embed=question_embed, view=None)

    @trivianight.command()
    @commands.has_any_role(*TRIVIA_NIGHT_ROLES)
    async def list(self, ctx: commands.Context) -> None:
        """
        Displays all the questions from the question bank.

        Questions are displayed in the following format:
        Q(number): Question description | :white_check_mark: if the question was used otherwise :x:.
        """
        question_list = self.questions.list_questions()
        if isinstance(question_list, Embed):
            await ctx.send(embed=question_list)
            return

        await ctx.send(question_list)

    @trivianight.command()
    @commands.has_any_role(*TRIVIA_NIGHT_ROLES)
    async def stop(self, ctx: commands.Context) -> None:
        """
        End the ongoing question to show the correct question.

        This command should be used if the question should be ended early or if the time limit fails
        """
        if self.questions.view.active_question is False:
            error_embed = Embed(
                title=choice(NEGATIVE_REPLIES),
                description="There is not an ongoing question to stop!",
                color=Colours.soft_red
            )
            await ctx.send(embed=error_embed)
            return

        self.questions.view.active_question = False

    @trivianight.command()
    @commands.has_any_role(*TRIVIA_NIGHT_ROLES)
    async def end(self, ctx: commands.Context) -> None:
        """
        Ends the trivia night event and displays the scoreboard view.

        The scoreboard view consists of the two scoreboards with the 30 players who got the highest points and the
        30 players who had the fastest average response time to a question where they got the question right.

        The scoreboard view also has a button where the user can see their own rank, points and average speed if they
        didn't make it onto the leaderboard.
        """
        if self.questions.view.active_question is True:
            error_embed = Embed(
                title=choice(NEGATIVE_REPLIES),
                description="You can't end the event while a question is ongoing!",
                color=Colours.soft_red
            )
            await ctx.send(embed=error_embed)
            return

        scoreboard_embed, scoreboard_view = await self.scoreboard.display()
        await ctx.send(embed=scoreboard_embed, view=scoreboard_view)


def setup(bot: Bot) -> None:
    """Load the TriviaNight cog."""
    bot.add_cog(TriviaNight(bot))

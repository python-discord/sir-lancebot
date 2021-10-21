import logging
from json import loads
from random import choice

from discord import Embed
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, POSITIVE_REPLIES
from ._questions import QuestionView, Questions
from ._scoreboard import Scoreboard, ScoreboardView


class TriviaNight(commands.Cog):
    """Cog for the Python Trivia Night event."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.scoreboard = Scoreboard()
        self.questions = Questions(self.scoreboard)

    @commands.group()
    async def trivianight(self, ctx: commands.Context) -> None:
        """No-op subcommand group for organizing different commands."""
        return

    @trivianight.command()
    async def load(self, ctx: commands.Context) -> None:
        """Load the JSON file provided into the questions."""
        json_text = (await ctx.message.attachments[0].read()).decode("utf8")
        serialized_json = loads(json_text)
        self.questions.view = QuestionView()
        logging.getLogger(__name__).debug(self.questions.view)
        self.scoreboard.view = ScoreboardView(self.bot)
        self.questions.set_questions(serialized_json)
        success_embed = Embed(
            title=choice(POSITIVE_REPLIES),
            description="The JSON was loaded successfully!",
            color=Colours.soft_green
        )
        await ctx.send(embed=success_embed)

    @trivianight.command()
    async def next(self, ctx: commands.Context) -> None:
        """Gets a random question from the unanswered question list and lets user choose the answer."""
        next_question = self.questions.next_question()
        if isinstance(next_question, Embed):
            await ctx.send(embed=next_question)
            return

        question_embed, question_view = self.questions.current_question()
        await ctx.send(embed=question_embed, view=question_view)

    @trivianight.command()
    async def stop(self, ctx: commands.Context) -> None:
        """End the ongoing question to show the correct question."""
        await ctx.send(embed=self.questions.end_question())

    @trivianight.command()
    async def end(self, ctx: commands.Context) -> None:
        """Ends the trivia night event and displays the scoreboard."""
        scoreboard_embed, scoreboard_view = await self.scoreboard.display()
        await ctx.send(embed=scoreboard_embed, view=scoreboard_view)


def setup(bot: Bot) -> None:
    """Load the TriviaNight cog."""
    bot.add_cog(TriviaNight(bot))

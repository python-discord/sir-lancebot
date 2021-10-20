from json import loads
from random import choice

from discord import Embed
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, POSITIVE_REPLIES
from ._questions import Questions
from ._scoreboard import Scoreboard


class TriviaNight(commands.Cog):
    """Cog for the Python Trivia Night event."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.scoreboard = Scoreboard(self.bot)
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
        self.questions.set_questions(serialized_json)
        success_embed = Embed(
            title=choice(POSITIVE_REPLIES),
            description="The JSON was loaded successfully!",
            color=Colours.soft_green
        )
        await ctx.send(embed=success_embed)


def setup(bot: Bot) -> None:
    """Load the TriviaNight cog."""
    bot.add_cog(TriviaNight(bot))

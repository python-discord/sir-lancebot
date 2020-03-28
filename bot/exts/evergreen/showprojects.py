import logging

from discord import Message
from discord.ext import commands

from bot.constants import Channels

log = logging.getLogger(__name__)


class ShowProjects(commands.Cog):
    """Cog that reacts to posts in the #show-your-projects."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lastPoster = 0  # Given 0 as the default last poster ID as no user can actually have 0 assigned to them

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        """Adds reactions to posts in #show-your-projects."""
        reactions = ["\U0001f44d", "\U00002764", "\U0001f440", "\U0001f389", "\U0001f680", "\U00002b50", "\U0001f6a9"]
        if (message.channel.id == Channels.show_your_projects
                and message.author.bot is False
                and message.author.id != self.lastPoster):
            for reaction in reactions:
                await message.add_reaction(reaction)

            self.lastPoster = message.author.id


def setup(bot: commands.Bot) -> None:
    """Show Projects Reaction Cog."""
    bot.add_cog(ShowProjects(bot))

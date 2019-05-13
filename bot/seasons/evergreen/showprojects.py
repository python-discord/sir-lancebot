import logging

from discord.ext import commands

from bot.constants import Channels

log = logging.getLogger(__name__)


class ShowProjects(commands.Cog):
    """Cog that reacts to posts in the #show-your-projects"""

    def __init__(self, bot):
        self.bot = bot
        self.lastPoster = 0  # Given 0 as the default last poster ID as no user can actually have 0 assigned to them

    @commands.Cog.listener()
    async def on_message(self, message):
        """Adds reactions to posts in #show-your-projects"""

        reactions = ["\U0001f44d", "\U00002764", "\U0001f440", "\U0001f389", "\U0001f680", "\U00002b50", "\U0001f6a9"]
        if message.channel.id == Channels.show_your_projects and message.author.id != 528937022996611082 \
                and message.author.id != self.lastPoster:
            for reaction in reactions:
                await message.add_reaction(reaction)

        self.lastPoster = message.author.id


def setup(bot):
    """Show Projects Reaction Cog"""

    bot.add_cog(ShowProjects(bot))
    log.info("ShowProjects cog loaded")

import logging

from discord.ext import commands

from bot.utils.movies import send_random_movie_embed

log = logging.getLogger(__name__)


class RomanceMovieFinder(commands.Cog):
    """A Cog that returns a random romance movie suggestion to a user."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="romancemovie")
    async def romance_movie(self, ctx: commands.Context) -> None:
        """Randomly selects a romance movie and displays information about it."""
        await send_random_movie_embed(bot=self.bot, ctx=ctx, icon=":sparkling_heart:", genre_code="10749", pages=20)


def setup(bot: commands.Bot) -> None:
    """Romance movie Cog load."""
    bot.add_cog(RomanceMovieFinder(bot))
    log.info("RomanceMovieFinder cog loaded")

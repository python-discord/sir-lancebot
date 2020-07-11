import logging

from discord.ext import commands
from http import HTTPStatus
import discord

log = logging.getLogger(__name__)


class StatusCats(commands.Cog):
    """Commands that give statuses described and visualized by cats."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['statuscat'])
    async def http_cat(self, ctx, code: int) -> None:
        """Sends an embed with an image of a cat, potraying the status code."""
        embed = discord.Embed(title=f'**Status: {code}**')
        embed.set_image(url=f'https://http.cat/{code}.jpg')

        try:
            HTTPStatus(code)

        except ValueError:
            embed.set_footer(text='Inputted status code does not exist.')

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Load the StatusCats cog."""
    bot.add_cog(StatusCats(bot))

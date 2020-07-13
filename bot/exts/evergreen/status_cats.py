from http import HTTPStatus

import discord
from discord.ext import commands


class StatusCats(commands.Cog):
    """Commands that give HTTP statuses described and visualized by cats."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['statuscat'])
    async def http_cat(self, ctx: commands.Context, code: int) -> None:
        """Sends an embed with an image of a cat, potraying the status code."""
        embed = discord.Embed(title=f'**Status: {code}**')

        try:
            HTTPStatus(code)

        except ValueError:
            embed.set_footer(text='Inputted status code does not exist.')

        else:
            embed.set_image(url=f'https://http.cat/{code}.jpg')

        finally:
            await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Load the StatusCats cog."""
    bot.add_cog(StatusCats(bot))

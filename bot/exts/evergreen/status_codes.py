from http import HTTPStatus

import discord
from discord.ext import commands

HTTP_DOG_URL = "https://httpstatusdogs.com/img/{code}.jpg"
HTTP_CAT_URL = "https://http.cat/{code}.jpg"


class HTTPStatusCodes(commands.Cog):
    """Commands that give HTTP statuses described and visualized by cats and dogs."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="http_status", aliases=("status", "httpstatus"))
    async def http_status_group(self, ctx: commands.Context) -> None:
        """Group containing dog and cat http status code commands."""
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @http_status_group.command(name='cat')
    async def http_cat(self, ctx: commands.Context, code: int) -> None:
        """Sends an embed with an image of a cat, portraying the status code."""
        embed = discord.Embed(title=f'**Status: {code}**')
        url = HTTP_CAT_URL.format(code=code)

        try:
            HTTPStatus(code)
            async with self.bot.http_session.get(url, allow_redirects=False) as response:
                if response.status != 404:
                    embed.set_image(url=url)
                else:
                    raise NotImplementedError

        except ValueError:
            embed.set_footer(text='Inputted status code does not exist.')

        except NotImplementedError:
            embed.set_footer(text='Inputted status code is not implemented by http.cat yet.')

        finally:
            await ctx.send(embed=embed)

    @http_status_group.command(name='dog')
    async def http_dog(self, ctx: commands.Context, code: int) -> None:
        """Sends an embed with an image of a dog, portraying the status code."""
        embed = discord.Embed(title=f'**Status: {code}**')
        url = HTTP_DOG_URL.format(code=code)

        try:
            HTTPStatus(code)
            async with self.bot.http_session.get(url, allow_redirects=False) as response:
                if response.status != 302:
                    embed.set_image(url=url)
                else:
                    raise NotImplementedError

        except ValueError:
            embed.set_footer(text='Inputted status code does not exist.')

        except NotImplementedError:
            embed.set_footer(text='Inputted status code is not implemented by httpstatusdogs.com yet.')

        finally:
            await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Load the HTTPStatusCodes cog."""
    bot.add_cog(HTTPStatusCodes(bot))

<<<<<<< HEAD
from http import HTTPStatus
from random import choice

import discord
from discord.ext.commands import Cog, commands

from bot.bot import Bot
=======
import discord
from discord.ext.commands import Bot, Cog, Context, group
>>>>>>> Removed HTTPStatus Dependency, enable broader Status Code Support

HTTP_DOG_URL = "https://httpstatusdogs.com/img/{code}.jpg"
HTTP_CAT_URL = "https://http.cat/{code}.jpg"
STATUS_TEMPLATE = '**Status: {code}**'
ERR_404 = 'Unable to find status Floof for {code}.'
ERR_UNKNOWN = 'Error attempting to retrieve status Floof for {code}.'


class HTTPStatusCodes(Cog):
    """Commands that give HTTP statuses described and visualized by cats and dogs."""

    def __init__(self, bot: Bot):
        self.bot = bot

<<<<<<< HEAD
    @commands.group(name="http_status", aliases=("status", "httpstatus"), invoke_without_command=True)
    async def http_status_group(self, ctx: commands.Context, code: int) -> None:
        """Choose a cat or dog randomly for the given status code."""
        subcmd = choice((self.http_cat, self.http_dog))
        await subcmd(ctx, code)

    @http_status_group.command(name="cat")
    async def http_cat(self, ctx: commands.Context, code: int) -> None:
        """Sends an embed with an image of a cat, portraying the status code."""
        embed = discord.Embed(title=f"**Status: {code}**")
        url = HTTP_CAT_URL.format(code=code)

        try:
            HTTPStatus(code)
            async with self.bot.http_session.get(url, allow_redirects=False) as response:
                if response.status != 404:
                    embed.set_image(url=url)
                else:
                    raise NotImplementedError

        except ValueError:
            embed.set_footer(text="Inputted status code does not exist.")

        except NotImplementedError:
            embed.set_footer(text="Inputted status code is not implemented by http.cat yet.")

        finally:
            await ctx.send(embed=embed)

    @http_status_group.command(name="dog")
    async def http_dog(self, ctx: commands.Context, code: int) -> None:
        """Sends an embed with an image of a dog, portraying the status code."""
        # These codes aren't server-friendly.
        if code in (304, 422):
            await self.http_cat(ctx, code)
            return

        embed = discord.Embed(title=f"**Status: {code}**")
        url = HTTP_DOG_URL.format(code=code)

        try:
            HTTPStatus(code)
            async with self.bot.http_session.get(url, allow_redirects=False) as response:
                if response.status != 302:
                    embed.set_image(url=url)
                else:
                    raise NotImplementedError

        except ValueError:
            embed.set_footer(text="Inputted status code does not exist.")

        except NotImplementedError:
            embed.set_footer(text="Inputted status code is not implemented by httpstatusdogs.com yet.")

        finally:
            await ctx.send(embed=embed)
=======
    @group(name="http_status", aliases=("status", "httpstatus"))
    async def http_status_group(self, ctx: Context) -> None:
        """Group containing dog and cat http status code commands."""
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @http_status_group.command(name='cat')
    async def http_cat(self, ctx: Context, code: int) -> None:
        """Assemble Cat URL and build Embed."""
        await self.build_embed(url=HTTP_CAT_URL.format(code), ctx=ctx, code=code)

    @http_status_group.command(name='dog')
    async def http_dog(self, ctx: Context, code: int) -> None:
        """Assemble Dog URL and build Embed."""
        await self.build_embed(url=HTTP_DOG_URL.format(code), ctx=ctx, code=code)

    async def build_embed(self, url: str, code: int, ctx: Context, ) -> None:
        """Attempt to build and dispatch embed. Append error message instead of something goes wrong."""
        async with self.bot.http_session.get(url, allow_redirects=False) as response:
            if 200 <= response.status <= 299:
                await ctx.send(embed=discord.Embed(title=STATUS_TEMPLATE.format(code), url=url))
            else:
                await ctx.send(embed=discord.Embed(
                    title=STATUS_TEMPLATE.format(code),
                    footer=ERR_404.format(code) if response.status == 404 else ERR_UNKNOWN.format(code))
                )
>>>>>>> Removed HTTPStatus Dependency, enable broader Status Code Support


def setup(bot: Bot) -> None:
    """Load the HTTPStatusCodes cog."""
    bot.add_cog(HTTPStatusCodes(bot))

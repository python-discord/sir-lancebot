from random import choice

import discord
from discord.ext import commands

from bot.bot import Bot

HTTP_DOG_URL = "https://httpstatusdogs.com/img/{code}.jpg"
HTTP_CAT_URL = "https://http.cat/{code}.jpg"
STATUS_TEMPLATE = "**Status: {code}**"
ERR_404 = "Unable to find status floof for {code}."
ERR_UNKNOWN = "Error attempting to retrieve status floof for {code}."
ERROR_LENGTH_EMBED = discord.Embed(
    title="Input status code does not exist",
    description="The range of valid status codes is 100 to 599",
)


class HTTPStatusCodes(commands.Cog):
    """
    Fetch an image depicting HTTP status codes as a dog or a cat.

    If neither animal is selected a cat or dog is chosen randomly for the given status code.
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.group(
        name="http_status",
        aliases=("status", "httpstatus"),
        invoke_without_command=True,
    )
    async def http_status_group(self, ctx: commands.Context, code: int) -> None:
        """Choose a cat or dog randomly for the given status code."""
        subcmd = choice((self.http_cat, self.http_dog))
        await subcmd(ctx, code)

    @http_status_group.command(name="cat")
    async def http_cat(self, ctx: commands.Context, code: int) -> None:
        """Send a cat version of the requested HTTP status code."""
        if code in range(100, 600):
            await self.build_embed(url=HTTP_CAT_URL.format(code=code), ctx=ctx, code=code)
            return
        await ctx.send(embed=ERROR_LENGTH_EMBED)

    @http_status_group.command(name="dog")
    async def http_dog(self, ctx: commands.Context, code: int) -> None:
        """Send a dog version of the requested HTTP status code."""
        if code in range(100, 600):
            await self.build_embed(url=HTTP_DOG_URL.format(code=code), ctx=ctx, code=code)
            return
        await ctx.send(embed=ERROR_LENGTH_EMBED)

    async def build_embed(self, url: str, ctx: commands.Context, code: int) -> None:
        """Attempt to build and dispatch embed. Append error message instead if something goes wrong."""
        async with self.bot.http_session.get(url, allow_redirects=False) as response:
            if response.status in range(200, 300):
                await ctx.send(
                    embed=discord.Embed(
                        title=STATUS_TEMPLATE.format(code=code)
                    ).set_image(url=url)
                )
            elif response.status in (302, 404):  # dog URL returns 302 instead of 404
                if "dog" in url:
                    await ctx.send(
                        embed=discord.Embed(
                            title=ERR_404.format(code=code)
                        ).set_image(url="https://httpstatusdogs.com/img/404.jpg")
                    )
                    return
                await ctx.send(
                    embed=discord.Embed(
                        title=ERR_404.format(code=code)
                    ).set_image(url="https://http.cat/404.jpg")
                )
            else:
                await ctx.send(
                    embed=discord.Embed(
                        title=STATUS_TEMPLATE.format(code=code)
                    ).set_footer(text=ERR_UNKNOWN.format(code=code))
                )


def setup(bot: Bot) -> None:
    """Load the HTTPStatusCodes cog."""
    bot.add_cog(HTTPStatusCodes(bot))

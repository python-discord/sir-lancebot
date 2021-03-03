import discord
from discord.ext import commands

HTTP_DOG_URL = "https://httpstatusdogs.com/img/{code}.jpg"
HTTP_CAT_URL = "https://http.cat/{code}.jpg"
STATUS_TEMPLATE = '**Status: {code}**'
ERR_404 = 'Unable to find status Floof for {code}.'
ERR_UNKNOWN = 'Error attempting to retrieve status Floof for {code}.'


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
        """Assemble Cat URL and build Embed."""
        await self.build_embed(url=HTTP_CAT_URL.format(code=code), ctx=ctx, code=code)

    @http_status_group.command(name='dog')
    async def http_dog(self, ctx: commands.Context, code: int) -> None:
        """Assemble Dog URL and build Embed."""
        await self.build_embed(url=HTTP_DOG_URL.format(code=code), ctx=ctx, code=code)

    async def build_embed(self, url: str, ctx: commands.Context, code: int) -> None:
        """Attempt to build and dispatch embed. Append error message instead if something goes wrong."""
        async with self.bot.http_session.get(url, allow_redirects=False) as response:
            if 200 <= response.status <= 299:
                await ctx.send(embed=discord.Embed(
                    title=STATUS_TEMPLATE.format(code=code)).set_image(url=url))
            elif 404 == response.status:
                await ctx.send(embed=discord.Embed(
                    title=ERR_404.format(code=code)).set_image(url=url)
                )
            else:
                await ctx.send(embed=discord.Embed(
                    title=STATUS_TEMPLATE.format(code=code), footer=ERR_UNKNOWN.format(code=code))
                )


def setup(bot: commands.Bot) -> None:
    """Load the HTTPStatusCodes cog."""
    bot.add_cog(HTTPStatusCodes(bot))

import discord
from discord.ext.commands import Bot, Cog, Context, group

HTTP_DOG_URL = "https://httpstatusdogs.com/img/{code}.jpg"
HTTP_CAT_URL = "https://http.cat/{code}.jpg"
STATUS_TEMPLATE = '**Status: {code}**'
ERR_404 = 'Unable to find status Floof for {code}.'
ERR_UNKNOWN = 'Error attempting to retrieve status Floof for {code}.'


class HTTPStatusCodes(Cog):
    """Commands that give HTTP statuses described and visualized by cats and dogs."""

    def __init__(self, bot: Bot):
        self.bot = bot

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
        """Attempt to build and dispatch embed. Append error message instead if something goes wrong."""
        async with self.bot.http_session.get(url, allow_redirects=False) as response:
            if 200 <= response.status <= 299:
                await ctx.send(embed=discord.Embed(
                    title=STATUS_TEMPLATE.format(code),
                    url=url
                ))
            elif 404 == response.status:
                await ctx.send(embed=discord.Embed(
                    title=ERR_404.format(code),
                    url=url
                ))
            else:
                await ctx.send(embed=discord.Embed(
                    title=STATUS_TEMPLATE.format(code),
                    footer=ERR_UNKNOWN.format(code)
                ))


def setup(bot: Bot) -> None:
    """Load the HTTPStatusCodes cog."""
    bot.add_cog(HTTPStatusCodes(bot))

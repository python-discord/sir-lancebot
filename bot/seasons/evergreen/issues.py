import json
import logging

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class Issues(commands.Cog):
    """Cog that allows users to retrieve issues from GitHub"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=("issues",))
    async def issue(self, ctx, number: int, repository: str = "seasonalbot", user: str = "python-discord"):
        url = f"https://api.github.com/repos/{user}/{repository}/issues/{str(number)}"
        status = {"404": f"Issue #{str(number)} doesn't exist in the repository {user}/{repository}.",
                  "403": f"Rate limit exceeded. Please wait a while before trying again!"}

        async with self.bot.http_session.get(url) as r:
            json_data = await r.json()

        if str(r.status) in status:
            return await ctx.send(status.get(str(r.status)))

        valid = discord.Embed(colour=0x00ff37)
        valid.add_field(name="Repository", value=f"{user}/{repository}", inline=False)
        valid.add_field(name="Issue Number", value=f"#{str(number)}", inline=False)
        valid.add_field(name="Status", value=json_data.get("state").title())
        valid.add_field(name="Link", value=url, inline=False)
        if len(json_data.get("body")) < 1024:
            valid.add_field(name="Description", value=json_data.get("body"), inline=False)
        await ctx.send(embed=valid)


def setup(bot):
    """Cog Retrieves Issues From Github"""

    bot.add_cog(Issues(bot))
    log.info("Issues cog loaded")

import logging

import discord
from discord.ext import commands

log = logging.getLogger(__name__)

icons = {"issue": "https://i.imgur.com/HFV0nv9.png",
         "issue-closed": "https://i.imgur.com/uZSX7as.png",
         "pull-request": "https://i.imgur.com/zHhnALX.png",
         "pull-request-closed": "https://i.imgur.com/JYmTn5P.png",
         "merge": "https://i.imgur.com/xzQZxXe.png"}

respValue = {404: "Issue/pull request not located! Please enter a valid number!",
             403: "rate limit has been hit! Please try again later!"}


class Issues(commands.Cog):
    """Cog that allows users to retrieve issues from GitHub"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=("pr",))
    async def issues(self, ctx, number: int, repository: str = "seasonalbot", user: str = "python-discord"):
        """Command to get issues/pull request from GitHub"""
        url = f"https://api.github.com/repos/{user}/{repository}/issues/{str(number)}"
        mergeURL = f"https://api.github.com/repos/{user}/{repository}/pulls/{str(number)}/merge"

        async with self.bot.http_session.get(url) as r:
            json_data = await r.json()

        if r.status in respValue:
            return await ctx.send(f"[{str(r.status)}] {respValue.get(r.status)}")

        if "issues" in json_data.get("html_url"):
            if json_data.get("state") == "open":
                iconURL = icons.get("issue")
            else:
                iconURL = icons.get("issue_closed")
        else:
            async with self.bot.http_session.get(mergeURL) as m:
                if json_data.get("state") == "open":
                    iconURL = icons.get("pull-request")
                elif m.status == 204:
                    iconURL = icons.get("merge")
                else:
                    iconURL = icons.get("pull-request-closed")

        resp = discord.Embed(colour=0x6CC644)
        resp.set_author(
            name=f"[{repository}] #{number} {json_data.get('title')}",
            url=json_data.get("html_url"),
            icon_url=iconURL)
        await ctx.send(embed=resp)


def setup(bot):
    """Cog Retrieves Issues From Github"""

    bot.add_cog(Issues(bot))
    log.info("Issues cog loaded")

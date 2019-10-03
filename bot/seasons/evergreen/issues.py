import logging

import discord
from discord.ext import commands

log = logging.getLogger(__name__)

icons = {"issue": "https://i.imgur.com/HFV0nv9.png",
         "issue-closed": "https://i.imgur.com/uZSX7as.png",
         "pull-request": "https://i.imgur.com/zHhnALX.png",
         "pull-request-closed": "https://i.imgur.com/JYmTn5P.png",
         "merge": "https://i.imgur.com/xzQZxXe.png"}

RESP_VALUE = {404: "Issue/pull request not located! Please enter a valid number!",
             403: "rate limit has been hit! Please try again later!"}


class Issues(commands.Cog):
    """Cog that allows users to retrieve issues from GitHub."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=("pr",))
    @override_in_channel()
    async def issue(self, ctx: commands.Context, number: int, repository: str = "seasonalbot",
                     user: str = "python-discord") -> None:
        """Command to get issues/pull request from GitHub."""
        url = f"https://api.github.com/repos/{user}/{repository}/issues/{str(number)}"
        mergeURL = f"https://api.github.com/repos/{user}/{repository}/pulls/{str(number)}/merge"

        async with self.bot.http_session.get(url) as r:
            json_data = await r.json()

        if r.status in RESP_VALUE:
            return await ctx.send(f"[{str(r.status)}] {RESP_VALUE.get(r.status)}")

        if "issues" in json_data.get("html_url"):
            if json_data.get("state") == "open":
                iconURL = icons.get("issue")
            else:
                iconURL = icons.get("issue_closed")
        else:
            async with self.bot.http_session.get(mergeURL) as m:
                if json_data.get("state") == "open":
                    iconURL = icons.get("pull-request")
                # when the status is 204 this means that the state of the PR is merged
                elif m.status == 204:
                    iconURL = icons.get("merge")
                # else by the process of elimination, the pull request has been closed
                else:
                    iconURL = icons.get("pull-request-closed")

        resp = discord.Embed(colour=0x6CC644)
        resp.set_author(
            name=f"[{repository}] #{number} {json_data.get('title')}",
            url=json_data.get("html_url"),
            icon_url=iconURL)
        await ctx.send(embed=resp)


def setup(bot: commands.Bot) -> None:
    """Cog Retrieves Issues From Github."""
    bot.add_cog(Issues(bot))
    log.info("Issues cog loaded")

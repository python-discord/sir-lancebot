import logging

import discord
from discord.ext import commands

from bot.constants import Colours
from bot.constants import Emojis
from bot.decorators import override_in_channel

log = logging.getLogger(__name__)

icons = {"issue": Emojis.issue,
         "issue-closed": Emojis.issue_closed,
         "pull-request": Emojis.pull_request,
         "pull-request-closed": Emojis.pull_request_closed,
         "merge": Emojis.merge}

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
        # the original call is made to the issues API endpoint
        # if a issue or PR exists then there will be something returned
        # if the word 'issues' is present within the response then we can simply pull the  data we need from the
        # return data received from the API
        if "issues" in json_data.get("html_url"):
            if json_data.get("state") == "open":
                iconURL = icons.get("issue")
            else:
                iconURL = icons.get("issue_closed")
        # if the word 'issues' is not contained within the returned data and there is no error code then we know that
        # the requested data is a pr, hence to get the specifics on it we have to call the PR API endpoint allowing us
        # to get the specific information in relation to the PR that is not provided via the issues endpoint
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

        resp = discord.Embed(colour=Colours.bright_green)
        resp.set_author(
            name=f"{iconURL} | [{repository}] #{number} {json_data.get('title')}",
            url=json_data.get("html_url"))
        await ctx.send(embed=resp)


def setup(bot: commands.Bot) -> None:
    """Cog Retrieves Issues From Github."""
    bot.add_cog(Issues(bot))
    log.info("Issues cog loaded")

import logging

import discord
from discord.ext import commands

from bot.constants import Colours, Emojis, WHITELISTED_CHANNELS
from bot.decorators import override_in_channel

log = logging.getLogger(__name__)

BAD_RESPONSE = {
    404: "Issue/pull request not located! Please enter a valid number!",
    403: "Rate limit has been hit! Please try again later!"
}


class Issues(commands.Cog):
    """Cog that allows users to retrieve issues from GitHub."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=("pr",))
    @override_in_channel(WHITELISTED_CHANNELS)
    async def issue(
        self, ctx: commands.Context, number: int, repository: str = "seasonalbot", user: str = "python-discord"
    ) -> None:
        """Command to retrieve issues from a GitHub repository."""
        url = f"https://api.github.com/repos/{user}/{repository}/issues/{number}"
        merge_url = f"https://api.github.com/repos/{user}/{repository}/pulls/{number}/merge"

        log.trace(f"Querying GH issues API: {url}")
        async with self.bot.http_session.get(url) as r:
            json_data = await r.json()

        if r.status in BAD_RESPONSE:
            log.warning(f"Received response {r.status} from: {url}")
            return await ctx.send(f"[{str(r.status)}] {BAD_RESPONSE.get(r.status)}")

        # The initial API request is made to the issues API endpoint, which will return information
        # if the issue or PR is present. However, the scope of information returned for PRs differs
        # from issues: if the 'issues' key is present in the response then we can pull the data we
        # need from the initial API call.
        if "issues" in json_data.get("html_url"):
            if json_data.get("state") == "open":
                icon_url = Emojis.issue
            else:
                icon_url = Emojis.issue_closed

        # If the 'issues' key is not contained in the API response and there is no error code, then
        # we know that a PR has been requested and a call to the pulls API endpoint is necessary
        # to get the desired information for the PR.
        else:
            log.trace(f"PR provided, querying GH pulls API for additional information: {merge_url}")
            async with self.bot.http_session.get(merge_url) as m:
                if json_data.get("state") == "open":
                    icon_url = Emojis.pull_request
                # When the status is 204 this means that the state of the PR is merged
                elif m.status == 204:
                    icon_url = Emojis.merge
                else:
                    icon_url = Emojis.pull_request_closed

        issue_url = json_data.get("html_url")
        description_text = f"[{repository}] #{number} {json_data.get('title')}"
        resp = discord.Embed(
            colour=Colours.bright_green,
            description=f"{icon_url} [{description_text}]({issue_url})"
        )
        resp.set_author(name="GitHub", url=issue_url)
        await ctx.send(embed=resp)


def setup(bot: commands.Bot) -> None:
    """Cog Retrieves Issues From Github."""
    bot.add_cog(Issues(bot))
    log.info("Issues cog loaded")

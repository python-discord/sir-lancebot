import logging

import discord
from discord.ext import commands

from bot.constants import Channels, Colours, WHITELISTED_CHANNELS
from bot.decorators import override_in_channel

log = logging.getLogger(__name__)
ISSUE_WHITELIST = WHITELISTED_CHANNELS + (Channels.seasonalbot_chat,)


class Issues(commands.Cog):
    """Cog that allows users to retrieve issues from GitHub."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=("issues",))
    @override_in_channel(ISSUE_WHITELIST)
    async def issue(
        self, ctx: commands.Context, number: int, repository: str = "seasonalbot", user: str = "python-discord"
    ) -> None:
        """Command to retrieve issues from a GitHub repository."""
        api_url = f"https://api.github.com/repos/{user}/{repository}/issues/{number}"
        failed_status = {
            404: f"Issue #{number} doesn't exist in the repository {user}/{repository}.",
            403: f"Rate limit exceeded. Please wait a while before trying again!"
        }

        async with self.bot.http_session.get(api_url) as r:
            json_data = await r.json()
            response_code = r.status

        if response_code in failed_status:
            return await ctx.send(failed_status[response_code])

        repo_url = f"https://github.com/{user}/{repository}"
        issue_embed = discord.Embed(colour=Colours.bright_green)
        issue_embed.add_field(name="Repository", value=f"[{user}/{repository}]({repo_url})", inline=False)
        issue_embed.add_field(name="Issue Number", value=f"#{number}", inline=False)
        issue_embed.add_field(name="Status", value=json_data["state"].title())
        issue_embed.add_field(name="Link", value=json_data["html_url"], inline=False)

        description = json_data["body"]
        if len(description) > 1024:
            placeholder = " [...]"
            description = f"{description[:1024 - len(placeholder)]}{placeholder}"

        issue_embed.add_field(name="Description", value=description, inline=False)

        await ctx.send(embed=issue_embed)


def setup(bot: commands.Bot) -> None:
    """Github Issues Cog Load."""
    bot.add_cog(Issues(bot))
    log.info("Issues cog loaded")

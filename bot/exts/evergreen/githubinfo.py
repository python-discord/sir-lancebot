import logging
import random
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

from bot.constants import NEGATIVE_REPLIES

log = logging.getLogger(__name__)


class GithubInfo(commands.Cog):
    """Fetches info from GitHub."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_data(self, url: str) -> dict:
        """Retrieve data as a dictionary."""
        async with self.bot.http_session.get(url) as r:
            return await r.json()

    @commands.command(name='github', aliases=['gh'])
    @commands.cooldown(1, 60, BucketType.user)
    async def get_github_info(self, ctx: commands.Context, username: Optional[str]) -> None:
        """
        Fetches a user's GitHub information.

        Username is optional and sends the help command if not specified.
        """
        if username is None:
            await ctx.invoke(self.bot.get_command('help'), 'github')
            ctx.command.reset_cooldown(ctx)
            return

        async with ctx.typing():
            user_data = await self.fetch_data(f"https://api.github.com/users/{username}")

            # User_data will not have a message key if the user exists
            if user_data.get('message') is not None:
                await ctx.send(embed=discord.Embed(title=random.choice(NEGATIVE_REPLIES),
                                                   description=f"The profile for `{username}` was not found.",
                                                   colour=discord.Colour.red()))
                return

            org_data = await self.fetch_data(user_data['organizations_url'])
            orgs = [f"[{org['login']}](https://github.com/{org['login']})" for org in org_data]
            orgs_to_add = ' | '.join(orgs)

            gists = user_data['public_gists']

            # Forming blog link
            if user_data['blog'].startswith("http"):  # Blog link is complete
                blog = user_data['blog']
            elif user_data['blog']:  # Blog exists but the link is not complete
                blog = f"https://{user_data['blog']}"
            else:
                blog = "No website link available"

            embed = discord.Embed(
                title=f"`{user_data['login']}`'s GitHub profile info",
                description=f"```{user_data['bio']}```\n" if user_data['bio'] is not None else "",
                colour=0x7289da,
                url=user_data['html_url'],
                timestamp=datetime.strptime(user_data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            )
            embed.set_thumbnail(url=user_data['avatar_url'])
            embed.set_footer(text="Account created at")

            if user_data['type'] == "User":

                embed.add_field(name="Followers",
                                value=f"[{user_data['followers']}]({user_data['html_url']}?tab=followers)")
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="Following",
                                value=f"[{user_data['following']}]({user_data['html_url']}?tab=following)")

            embed.add_field(name="Public repos",
                            value=f"[{user_data['public_repos']}]({user_data['html_url']}?tab=repositories)")
            embed.add_field(name="\u200b", value="\u200b")

            if user_data['type'] == "User":
                embed.add_field(name="Gists", value=f"[{gists}](https://gist.github.com/{username})")

                embed.add_field(name=f"Organization{'s' if len(orgs)!=1 else ''}",
                                value=orgs_to_add if orgs else "No organizations")
                embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Website", value=blog)

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Adding the cog to the bot."""
    bot.add_cog(GithubInfo(bot))

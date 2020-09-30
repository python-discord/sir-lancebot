import logging
import aiohttp
from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

log = logging.getLogger(__name__)


class GithubInfo(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_data(self, url: str) -> dict:
        """Retrieve data as a dictionary"""

        async with aiohttp.ClientSession() as cs:
            async with cs.get(url) as r:
                return await r.json()

    @commands.command(name='github', aliases=['gh'])
    @commands.cooldown(1, 5, BucketType.user)
    async def get_github_info(self, ctx: commands.Context, username: str = 'python-discord') -> None:
        """Fetches a user's GitHub information

        User defaults to python-discord

        Usage: .gh [username]
        """

        # fetch user data
        user_data = await self.fetch_data(f"https://api.github.com/users/{username}")

        # user_data will not have a message key if the user exists
        if user_data.get('message') is not None:
            return await ctx.send(embed=discord.Embed(title=f"The profile `{username}` was not found", colour=0xff0022))

        # fetching organization data and forming the organization string
        org_data = await self.fetch_data(user_data['organizations_url'])

        orgs = [f"[{org['login']}](https://github.com/{org['login']})" for org in org_data]
        orgs_to_add = ' | '.join(orgs)

        # fetching starred repos data
        starred_data = await self.fetch_data(user_data['starred_url'])

        # forming blog link
        if user_data['blog'].startswith("http"):  # blog link is clickable
            blog = f"[Direct link]({user_data['blog']})"
        elif user_data['blog']:  # blog exists but the link is not clickable
            blog = f"[Direct link](https://{user_data['blog']})"
        else:  # blog does not exist
            blog = "No blog link available"

        # building embed
        embed = discord.Embed(
            title=f"`{user_data['login']}`'s GitHub profile info",
            description=f"```{user_data['bio']}```\n" if user_data['bio'] is not None else "",
            colour=0xf5faf6,
            url=user_data['html_url'],
            timestamp=datetime.strptime(user_data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        )
        embed.set_thumbnail(url=user_data['avatar_url'])
        embed.set_footer(text="Account created at")

        embed.add_field(name="Followers", value=f"[{user_data['followers']}]{user_data['html_url']}?tab=followers)")
        embed.add_field(name="\u200b", value="\u200b")  # zero width space
        embed.add_field(name="Following", value=f"[{user_data['following']}]{user_data['html_url']}?tab=following)")

        embed.add_field(name="Public repos",
                        value=f"[{user_data['public_repos']}]{user_data['html_url']}?tab=repositories)")
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Starred repos", value=f"[{len(starred_data)}]{user_data['html_url']}?tab=stars)")

        embed.add_field(name=f"Organization{'s' if len(orgs)!=1 else ''}",
                        value=orgs_to_add if orgs else "No organizations")
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Blog", value=blog)

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Load the cog"""
    bot.add_cog(GithubInfo(bot))

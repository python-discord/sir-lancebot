import logging
import random
from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

from bot.constants import NEGATIVE_REPLIES, Colours
from bot.exts.utils.extensions import invoke_help_command

log = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"


class GithubInfo(commands.Cog):
    """Fetches info from GitHub."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_data(self, url: str) -> dict:
        """Retrieve data as a dictionary."""
        async with self.bot.http_session.get(url) as r:
            return await r.json()

    @commands.group(name='github', aliases=('gh', 'git'))
    @commands.cooldown(1, 10, BucketType.user)
    async def github_group(self, ctx: commands.Context) -> None:
        """Commands for finding info related to Github."""
        if ctx.invoked_subcommand is None:
            await invoke_help_command(ctx)

    @github_group.command(name='user', aliases=('userinfo',))
    async def github_user_info(self, ctx: commands.Context, username: str) -> None:
        """
        Fetches a user's GitHub information.

        Username is optional and sends the help command if not specified.
        """
        async with ctx.typing():
            user_data = await self.fetch_data(f"{GITHUB_API_URL}/users/{username}")

            # User_data will not have a message key if the user exists
            if user_data.get('message') is not None:
                embed = discord.Embed(
                    title=random.choice(NEGATIVE_REPLIES),
                    description=f"The profile for `{username}` was not found.",
                    colour=Colours.soft_red
                )

                await ctx.send()
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
                colour=discord.Colour.blurple(),
                url=user_data['html_url'],
                timestamp=datetime.strptime(user_data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            )
            embed.set_thumbnail(url=user_data['avatar_url'])
            embed.set_footer(text="Account created at")

            if user_data['type'] == "User":

                embed.add_field(
                    name="Followers",
                    value=f"[{user_data['followers']}]({user_data['html_url']}?tab=followers)"
                )
                embed.add_field(
                    name="Following",
                    value=f"[{user_data['following']}]({user_data['html_url']}?tab=following)"
                )

            embed.add_field(
                name="Public repos",
                value=f"[{user_data['public_repos']}]({user_data['html_url']}?tab=repositories)"
            )

            if user_data['type'] == "User":
                embed.add_field(name="Gists", value=f"[{gists}](https://gist.github.com/{username})")

                embed.add_field(
                    name=f"Organization{'s' if len(orgs)!=1 else ''}",
                    value=orgs_to_add if orgs else "No organizations"
                )
            embed.add_field(name="Website", value=blog)

        await ctx.send(embed=embed)

    @github_group.command(name='repository', aliases=('repo',))
    async def github_repo_info(self, ctx: commands.Context, repo: str) -> None:
        """
        Fetches a repositories' GitHub information. The repository should look like `user/reponame`.

        Repository is optional and sends the help command if not specified.
        """
        async with ctx.typing():
            repo_data = await self.fetch_data(f"{GITHUB_API_URL}/repos/{repo}")

            # There won't be a message key if this repo exists
            if repo_data.get('message') is not None:
                embed = discord.Embed(
                    title=random.choice(NEGATIVE_REPLIES),
                    description="The requested repository was not found.",
                    colour=Colours.soft_red
                )

                await ctx.send(embed=embed)
                return

        repo_owner = repo_data['owner']

        parent = repo_data.get('parent')

        embed = discord.Embed(
            title=f"{repo_data['name']}",
            description=repo_data["description"],
            colour=0x7289da,
            url=repo_data['html_url'],
            timestamp=datetime.strptime(repo_data['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
        )

        # If it's a fork, then it will have a parent key
        if parent:
            embed.description += f"\n\nForked from [{parent['full_name']}]({parent['html_url']})"

        embed.set_author(
            name=repo_owner["login"],
            url=repo_owner["html_url"],
            icon_url=repo_owner["avatar_url"]
        )

        repo_created_at = datetime.strptime(repo_data['created_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y")

        embed.set_footer(
            text=(
                f"{repo_data['forks_count']} "
                f"⑂  •  {repo_data['stargazers_count']} ⭐ •  Created At {repo_created_at}  • "
                " Last commit "
            )
        )

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Adding the cog to the bot."""
    bot.add_cog(GithubInfo(bot))

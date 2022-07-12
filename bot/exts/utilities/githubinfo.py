import logging
import random
import re
import typing as t
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote

import discord
from aiohttp import ClientResponse
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, ERROR_REPLIES, Emojis, NEGATIVE_REPLIES, Tokens
from bot.exts.core.extensions import invoke_help_command

log = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"

REQUEST_HEADERS = {
    "Accept": "application/vnd.github.v3+json"
}

REPOSITORY_ENDPOINT = "https://api.github.com/orgs/{org}/repos?per_page=100&type=public"
ISSUE_ENDPOINT = "https://api.github.com/repos/{user}/{repository}/issues/{number}"
PR_ENDPOINT = "https://api.github.com/repos/{user}/{repository}/pulls/{number}"

if Tokens.github:
    REQUEST_HEADERS["Authorization"] = f"token {Tokens.github}"

CODE_BLOCK_RE = re.compile(
    r"^`([^`\n]+)`"   # Inline codeblock
    r"|```(.+?)```",  # Multiline codeblock
    re.DOTALL | re.MULTILINE
)

# Maximum number of issues in one message
MAXIMUM_ISSUES = 5

# Regex used when looking for automatic linking in messages
# regex101 of current regex https://regex101.com/r/V2ji8M/6
AUTOMATIC_REGEX = re.compile(
    r"((?P<org>[a-zA-Z0-9][a-zA-Z0-9\-]{1,39})\/)?(?P<repo>[\w\-\.]{1,100})#(?P<number>[0-9]+)"
)


@dataclass(eq=True, frozen=True)
class FoundIssue:
    """Dataclass representing an issue found by the regex."""

    organisation: t.Optional[str]
    repository: str
    number: str


@dataclass(eq=True, frozen=True)
class FetchError:
    """Dataclass representing an error while fetching an issue."""

    return_code: int
    message: str


@dataclass(eq=True, frozen=True)
class IssueState:
    """Dataclass representing the state of an issue."""

    repository: str
    number: int
    url: str
    title: str
    emoji: str


class GithubInfo(commands.Cog):
    """A Cog that fetches info from GitHub."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.repos = []

    @staticmethod
    def remove_codeblocks(message: str) -> str:
        """Remove any codeblock in a message."""
        return CODE_BLOCK_RE.sub("", message)

    async def fetch_issue(
        self,
        number: int,
        repository: str,
        user: str
    ) -> t.Union[IssueState, FetchError]:
        """
        Retrieve an issue from a GitHub repository.

        Returns IssueState on success, FetchError on failure.
        """
        url = ISSUE_ENDPOINT.format(user=user, repository=repository, number=number)
        pulls_url = PR_ENDPOINT.format(user=user, repository=repository, number=number)

        json_data, r = await self.fetch_data(url)

        if r.status == 403:
            if r.headers.get("X-RateLimit-Remaining") == "0":
                log.info(f"Ratelimit reached while fetching {url}")
                return FetchError(403, "Ratelimit reached, please retry in a few minutes.")
            return FetchError(403, "Cannot access issue.")
        elif r.status in (404, 410):
            return FetchError(r.status, "Issue not found.")
        elif r.status != 200:
            return FetchError(r.status, "Error while fetching issue.")

        # The initial API request is made to the issues API endpoint, which will return information
        # if the issue or PR is present. However, the scope of information returned for PRs differs
        # from issues: if the 'issues' key is present in the response then we can pull the data we
        # need from the initial API call.
        if "issues" in json_data["html_url"]:
            if json_data.get("state") == "open":
                emoji = Emojis.issue_open
            else:
                emoji = Emojis.issue_closed

        # If the 'issues' key is not contained in the API response and there is no error code, then
        # we know that a PR has been requested and a call to the pulls API endpoint is necessary
        # to get the desired information for the PR.
        else:
            pull_data, _ = await self.fetch_data(pulls_url)
            if pull_data["draft"]:
                emoji = Emojis.pull_request_draft
            elif pull_data["state"] == "open":
                emoji = Emojis.pull_request_open
            # When 'merged_at' is not None, this means that the state of the PR is merged
            elif pull_data["merged_at"] is not None:
                emoji = Emojis.pull_request_merged
            else:
                emoji = Emojis.pull_request_closed

        issue_url = json_data.get("html_url")

        return IssueState(repository, number, issue_url, json_data.get("title", ""), emoji)

    @staticmethod
    def format_embed(
        results: t.List[t.Union[IssueState, FetchError]]
    ) -> discord.Embed:
        """Take a list of IssueState or FetchError and format a Discord embed for them."""
        description_list = []

        for result in results:
            if isinstance(result, IssueState):
                description_list.append(f"{result.emoji} [{result.title}]({result.url})")
            elif isinstance(result, FetchError):
                description_list.append(f":x: [{result.return_code}] {result.message}")

        resp = discord.Embed(
            colour=Colours.bright_green,
            description="\n".join(description_list)
        )

        resp.set_author(name="GitHub")
        return resp

    @commands.group(name="github", aliases=("gh", "git"))
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def github_group(self, ctx: commands.Context) -> None:
        """Commands for finding information related to GitHub."""
        if ctx.invoked_subcommand is None:
            await invoke_help_command(ctx)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Automatic issue linking.

        Listener to retrieve issue(s) from a GitHub repository using automatic linking if matching <org>/<repo>#<issue>.
        """
        # Ignore bots
        if message.author.bot:
            return

        issues = [
            FoundIssue(*match.group("org", "repo", "number"))
            for match in AUTOMATIC_REGEX.finditer(self.remove_codeblocks(message.content))
        ]
        links = []

        if issues:
            # Block this from working in DMs
            if not message.guild:
                return

            log.trace(f"Found {issues = }")
            # Remove duplicates
            issues = list(dict.fromkeys(issues))

            if len(issues) > MAXIMUM_ISSUES:
                embed = discord.Embed(
                    title=random.choice(ERROR_REPLIES),
                    color=Colours.soft_red,
                    description=f"Too many issues/PRs! (maximum of {MAXIMUM_ISSUES})"
                )
                await message.channel.send(embed=embed, delete_after=5)
                return

            for repo_issue in issues:
                result = await self.fetch_issue(
                    int(repo_issue.number),
                    repo_issue.repository,
                    repo_issue.organisation or "python-discord"
                )
                if isinstance(result, IssueState):
                    links.append(result)

        if not links:
            return

        resp = self.format_embed(links)
        await message.channel.send(embed=resp)

    async def fetch_data(self, url: str) -> tuple[dict[str], ClientResponse]:
        """Retrieve data as a dictionary and the response in a tuple."""
        log.trace(f"Querying GH issues API: {url}")
        async with self.bot.http_session.get(url, headers=REQUEST_HEADERS) as r:
            return await r.json(), r

    @github_group.command(name="user", aliases=("userinfo",))
    async def github_user_info(self, ctx: commands.Context, username: str) -> None:
        """Fetches a user's GitHub information."""
        async with ctx.typing():
            user_data, _ = await self.fetch_data(f"{GITHUB_API_URL}/users/{username}")

            # User_data will not have a message key if the user exists
            if "message" in user_data:
                embed = discord.Embed(
                    title=random.choice(NEGATIVE_REPLIES),
                    description=f"The profile for `{username}` was not found.",
                    colour=Colours.soft_red
                )

                await ctx.send(embed=embed)
                return

            org_data, _ = await self.fetch_data(user_data["organizations_url"])
            orgs = [f"[{org['login']}](https://github.com/{org['login']})" for org in org_data]
            orgs_to_add = " | ".join(orgs)

            gists = user_data["public_gists"]

            # Forming blog link
            if user_data["blog"].startswith("http"):  # Blog link is complete
                blog = user_data["blog"]
            elif user_data["blog"]:  # Blog exists but the link is not complete
                blog = f"https://{user_data['blog']}"
            else:
                blog = "No website link available"

            embed = discord.Embed(
                title=f"`{user_data['login']}`'s GitHub profile info",
                description=f"```\n{user_data['bio']}\n```\n" if user_data["bio"] else "",
                colour=discord.Colour.og_blurple(),
                url=user_data["html_url"],
                timestamp=datetime.strptime(user_data["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            )
            embed.set_thumbnail(url=user_data["avatar_url"])
            embed.set_footer(text="Account created at")

            if user_data["type"] == "User":

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

            if user_data["type"] == "User":
                embed.add_field(name="Gists", value=f"[{gists}](https://gist.github.com/{quote(username, safe='')})")

                embed.add_field(
                    name=f"Organization{'s' if len(orgs)!=1 else ''}",
                    value=orgs_to_add if orgs else "No organizations."
                )
            embed.add_field(name="Website", value=blog)

        await ctx.send(embed=embed)

    @github_group.command(name='repository', aliases=('repo',))
    async def github_repo_info(self, ctx: commands.Context, *repo: str) -> None:
        """
        Fetches a repositories' GitHub information.

        The repository should look like `user/reponame` or `user reponame`.
        """
        repo = "/".join(repo)
        if repo.count("/") != 1:
            embed = discord.Embed(
                title=random.choice(NEGATIVE_REPLIES),
                description="The repository should look like `user/reponame` or `user reponame`.",
                colour=Colours.soft_red
            )

            await ctx.send(embed=embed)
            return

        async with ctx.typing():
            repo_data, _ = await self.fetch_data(f"{GITHUB_API_URL}/repos/{quote(repo)}")

            # There won't be a message key if this repo exists
            if "message" in repo_data:
                embed = discord.Embed(
                    title=random.choice(NEGATIVE_REPLIES),
                    description="The requested repository was not found.",
                    colour=Colours.soft_red
                )

                await ctx.send(embed=embed)
                return

        embed = discord.Embed(
            title=repo_data["name"],
            description=repo_data["description"],
            colour=discord.Colour.og_blurple(),
            url=repo_data["html_url"]
        )

        # If it's a fork, then it will have a parent key
        try:
            parent = repo_data["parent"]
            embed.description += f"\n\nForked from [{parent['full_name']}]({parent['html_url']})"
        except KeyError:
            log.debug("Repository is not a fork.")

        repo_owner = repo_data["owner"]

        embed.set_author(
            name=repo_owner["login"],
            url=repo_owner["html_url"],
            icon_url=repo_owner["avatar_url"]
        )

        repo_created_at = datetime.strptime(repo_data["created_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y")
        last_pushed = datetime.strptime(repo_data["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y at %H:%M")

        embed.set_footer(
            text=(
                f"{repo_data['forks_count']} ⑂ "
                f"• {repo_data['stargazers_count']} ⭐ "
                f"• Created At {repo_created_at} "
                f"• Last Commit {last_pushed}"
            )
        )

        await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Load the GithubInfo cog."""
    bot.add_cog(GithubInfo(bot))

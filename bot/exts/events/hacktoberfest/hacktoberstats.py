import logging
import random
import re
from collections import Counter
from datetime import UTC, datetime, timedelta
from urllib.parse import quote_plus

import discord
from async_rediscache import RedisCache
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, Month, NEGATIVE_REPLIES, Tokens
from bot.utils.decorators import in_month

log = logging.getLogger(__name__)

CURRENT_YEAR = datetime.now(tz=UTC).year  # Used to construct GH API query
PRS_FOR_SHIRT = 4  # Minimum number of PRs before a shirt is awarded
REVIEW_DAYS = 14  # number of days needed after PR can be mature

REQUEST_HEADERS = {"User-Agent": "Python Discord Hacktoberbot"}
# using repo topics API during preview period requires an accept header
GITHUB_TOPICS_ACCEPT_HEADER = {"Accept": "application/vnd.github.mercy-preview+json"}
if GITHUB_TOKEN := Tokens.github:
    REQUEST_HEADERS["Authorization"] = f"token {GITHUB_TOKEN.get_secret_value()}"
    GITHUB_TOPICS_ACCEPT_HEADER["Authorization"] = f"token {GITHUB_TOKEN.get_secret_value()}"

GITHUB_NONEXISTENT_USER_MESSAGE = (
    "The listed users cannot be searched either because the users do not exist "
    "or you do not have permission to view the users."
)


class HacktoberStats(commands.Cog):
    """Hacktoberfest statistics Cog."""

    # Stores mapping of user IDs and GitHub usernames
    linked_accounts = RedisCache()

    def __init__(self, bot: Bot):
        self.bot = bot

    @in_month(Month.SEPTEMBER, Month.OCTOBER, Month.NOVEMBER)
    @commands.group(name="hacktoberstats", aliases=("hackstats",), invoke_without_command=True)
    async def hacktoberstats_group(self, ctx: commands.Context, github_username: str = None) -> None:
        """
        Display an embed for a user's Hacktoberfest contributions.

        If invoked without a subcommand or github_username, get the invoking user's stats if they've
        linked their Discord name to GitHub using .stats link. If invoked with a github_username,
        get that user's contributions
        """
        if not github_username:
            author_id, author_mention = self._author_mention_from_context(ctx)

            if await self.linked_accounts.contains(author_id):
                github_username = await self.linked_accounts.get(author_id)
                logging.info(f"Getting stats for {author_id} linked GitHub account '{github_username}'")
            else:
                msg = (
                    f"{author_mention}, you have not linked a GitHub account\n\n"
                    f"You can link your GitHub account using:\n```\n{ctx.prefix}hackstats link github_username\n```\n"
                    f"Or query GitHub stats directly using:\n```\n{ctx.prefix}hackstats github_username\n```"
                )
                await ctx.send(msg)
                return

        await self.get_stats(ctx, github_username)

    @in_month(Month.SEPTEMBER, Month.OCTOBER, Month.NOVEMBER)
    @hacktoberstats_group.command(name="link")
    async def link_user(self, ctx: commands.Context, github_username: str = None) -> None:
        """
        Link the invoking user's Github github_username to their Discord ID.

        Linked users are stored in Redis: User ID => GitHub Username.
        """
        author_id, author_mention = self._author_mention_from_context(ctx)
        if github_username:
            if await self.linked_accounts.contains(author_id):
                old_username = await self.linked_accounts.get(author_id)
                log.info(f"{author_id} has changed their github link from '{old_username}' to '{github_username}'")
                await ctx.send(f"{author_mention}, your GitHub username has been updated to: '{github_username}'")
            else:
                log.info(f"{author_id} has added a github link to '{github_username}'")
                await ctx.send(f"{author_mention}, your GitHub username has been added")

            await self.linked_accounts.set(author_id, github_username)
        else:
            log.info(f"{author_id} tried to link a GitHub account but didn't provide a username")
            await ctx.send(f"{author_mention}, a GitHub username is required to link your account")

    @in_month(Month.SEPTEMBER, Month.OCTOBER, Month.NOVEMBER)
    @hacktoberstats_group.command(name="unlink")
    async def unlink_user(self, ctx: commands.Context) -> None:
        """Remove the invoking user's account link from the log."""
        author_id, author_mention = self._author_mention_from_context(ctx)

        stored_user = await self.linked_accounts.pop(author_id, None)
        if stored_user:
            await ctx.send(f"{author_mention}, your GitHub profile has been unlinked")
            logging.info(f"{author_id} has unlinked their GitHub account")
        else:
            await ctx.send(f"{author_mention}, you do not currently have a linked GitHub account")
            logging.info(f"{author_id} tried to unlink their GitHub account but no account was linked")

    async def get_stats(self, ctx: commands.Context, github_username: str) -> None:
        """
        Query GitHub's API for PRs created by a GitHub user during the month of October.

        PRs with an 'invalid' or 'spam' label are ignored

        For PRs created after October 3rd, they have to be in a repository that has a
        'hacktoberfest' topic, unless the PR is labelled 'hacktoberfest-accepted' for it
        to count.

        If a valid github_username is provided, an embed is generated and posted to the channel

        Otherwise, post a helpful error message
        """
        async with ctx.typing():
            prs = await self.get_october_prs(github_username)

            if prs is None:  # Will be None if the user was not found
                await ctx.send(
                    embed=discord.Embed(
                        title=random.choice(NEGATIVE_REPLIES),
                        description=f"GitHub user `{github_username}` was not found.",
                        colour=discord.Colour.red()
                    )
                )
                return

            if prs:
                stats_embed = await self.build_embed(github_username, prs)
                await ctx.send("Here are some stats!", embed=stats_embed)
            else:
                await ctx.send(f"No valid Hacktoberfest PRs found for '{github_username}'")

    async def build_embed(self, github_username: str, prs: list[dict]) -> discord.Embed:
        """Return a stats embed built from github_username's PRs."""
        logging.info(f"Building Hacktoberfest embed for GitHub user: '{github_username}'")
        in_review, accepted = await self._categorize_prs(prs)

        n = len(accepted) + len(in_review)  # Total number of PRs
        if n >= PRS_FOR_SHIRT:
            shirtstr = f"**{github_username} is eligible for a T-shirt or a tree!**"
        elif n == PRS_FOR_SHIRT - 1:
            shirtstr = f"**{github_username} is 1 PR away from a T-shirt or a tree!**"
        else:
            shirtstr = f"**{github_username} is {PRS_FOR_SHIRT - n} PRs away from a T-shirt or a tree!**"

        stats_embed = discord.Embed(
            title=f"{github_username}'s Hacktoberfest",
            color=Colours.purple,
            description=(
                f"{github_username} has made {n} valid "
                f"{self._contributionator(n)} in "
                f"October\n\n"
                f"{shirtstr}\n\n"
            )
        )

        stats_embed.set_thumbnail(url=f"https://www.github.com/{github_username}.png")
        stats_embed.set_author(
            name="Hacktoberfest",
            url="https://hacktoberfest.digitalocean.com",
            icon_url="https://avatars1.githubusercontent.com/u/35706162?s=200&v=4"
        )

        # This will handle when no PRs in_review or accepted
        review_str = self._build_prs_string(in_review, github_username) or "None"
        accepted_str = self._build_prs_string(accepted, github_username) or "None"
        stats_embed.add_field(
            name=":clock1: In Review",
            value=review_str
        )
        stats_embed.add_field(
            name=":tada: Accepted",
            value=accepted_str
        )

        logging.info(f"Hacktoberfest PR built for GitHub user '{github_username}'")
        return stats_embed

    async def get_october_prs(self, github_username: str) -> list[dict] | None:
        """
        Query GitHub's API for PRs created during the month of October by github_username.

        PRs with an 'invalid' or 'spam' label are ignored unless it is merged or approved

        For PRs created after October 3rd, they have to be in a repository that has a
        'hacktoberfest' topic, unless the PR is labelled 'hacktoberfest-accepted' for it
        to count.

        If PRs are found, return a list of dicts with basic PR information

        For each PR:
        {
            "repo_url": str
            "repo_shortname": str (e.g. "python-discord/sir-lancebot")
            "created_at": datetime.datetime
            "number": int
        }

        Otherwise, return empty list.
        None will be returned when the GitHub user was not found.
        """
        log.info(f"Fetching Hacktoberfest Stats for GitHub user: '{github_username}'")
        base_url = "https://api.github.com/search/issues"
        action_type = "pr"
        is_query = "public"
        not_query = "draft"
        date_range = f"{CURRENT_YEAR}-09-30T10:00Z..{CURRENT_YEAR}-11-01T12:00Z"
        per_page = "300"
        query_params = (
            f"+type:{action_type}"
            f"+is:{is_query}"
            f"+author:{quote_plus(github_username)}"
            f"+-is:{not_query}"
            f"+created:{date_range}"
            f"&per_page={per_page}"
        )

        log.debug(f"GitHub query parameters generated: {query_params}")

        jsonresp = await self._fetch_url(base_url, REQUEST_HEADERS, {"q": query_params})
        if "message" in jsonresp:
            # One of the parameters is invalid, short circuit for now
            api_message = jsonresp["errors"][0]["message"]

            # Ignore logging non-existent users or users we do not have permission to see
            if api_message == GITHUB_NONEXISTENT_USER_MESSAGE:
                log.debug(f"No GitHub user found named '{github_username}'")
                return None
            log.error(f"GitHub API request for '{github_username}' failed with message: {api_message}")
            return []  # No October PRs were found due to error

        if jsonresp["total_count"] == 0:
            # Short circuit if there aren't any PRs
            log.info(f"No October PRs found for GitHub user: '{github_username}'")
            return []

        logging.info(f"Found {len(jsonresp['items'])} Hacktoberfest PRs for GitHub user: '{github_username}'")
        outlist = []  # list of pr information dicts that will get returned
        oct3 = datetime(int(CURRENT_YEAR), 10, 3, 23, 59, 59, tzinfo=UTC)
        hackto_topics = {}  # cache whether each repo has the appropriate topic (bool values)
        for item in jsonresp["items"]:
            shortname = self._get_shortname(item["repository_url"])
            itemdict = {
                "repo_url": f"https://www.github.com/{shortname}",
                "repo_shortname": shortname,
                "created_at": datetime.strptime(
                    item["created_at"], "%Y-%m-%dT%H:%M:%SZ"
                ).replace(tzinfo=UTC),
                "number": item["number"]
            }

            # If the PR has 'invalid' or 'spam' labels, the PR must be
            # either merged or approved for it to be included
            if self._has_label(item, ["invalid", "spam"]) and not await self._is_accepted(itemdict):
                continue

            # PRs before oct 3 no need to check for topics
            # continue the loop if 'hacktoberfest-accepted' is labelled then
            # there is no need to check for its topics
            if itemdict["created_at"] < oct3:
                outlist.append(itemdict)
                continue

            # Checking PR's labels for "hacktoberfest-accepted"
            if self._has_label(item, "hacktoberfest-accepted"):
                outlist.append(itemdict)
                continue

            # No need to query GitHub if repo topics are fetched before already
            if hackto_topics.get(shortname):
                outlist.append(itemdict)
                continue
            # Fetch topics for the PR's repo
            topics_query_url = f"https://api.github.com/repos/{shortname}/topics"
            log.debug(f"Fetching repo topics for {shortname} with url: {topics_query_url}")
            jsonresp2 = await self._fetch_url(topics_query_url, GITHUB_TOPICS_ACCEPT_HEADER)
            if jsonresp2.get("names") is None:
                log.error(f"Error fetching topics for {shortname}: {jsonresp2['message']}")
                continue  # Assume the repo doesn't have the `hacktoberfest` topic if API  request errored

            # PRs after oct 3 that doesn't have 'hacktoberfest-accepted' label
            # must be in repo with 'hacktoberfest' topic
            if "hacktoberfest" in jsonresp2["names"]:
                hackto_topics[shortname] = True  # Cache result in the dict for later use if needed
                outlist.append(itemdict)
        return outlist

    async def _fetch_url(self, url: str, headers: dict, params: dict) -> dict:
        """Retrieve API response from URL."""
        async with self.bot.http_session.get(url, headers=headers, params=params) as resp:
            return await resp.json()

    @staticmethod
    def _has_label(pr: dict, labels: list[str] | str) -> bool:
        """
        Check if a PR has label 'labels'.

        'labels' can be a string or a list of strings, if it's a list of strings
        it will return true if any of the labels match.
        """
        if not pr.get("labels"):  # if PR has no labels
            return False
        if isinstance(labels, str) and any(label["name"].casefold() == labels for label in pr["labels"]):
            return True
        for item in labels:  # noqa: SIM110
            if any(label["name"].casefold() == item for label in pr["labels"]):
                return True
        return False

    async def _is_accepted(self, pr: dict) -> bool:
        """Check if a PR is merged, approved, or labelled hacktoberfest-accepted."""
        # checking for merge status
        query_url = f"https://api.github.com/repos/{pr['repo_shortname']}/pulls/{pr['number']}"
        jsonresp = await self._fetch_url(query_url, REQUEST_HEADERS)

        if message := jsonresp.get("message"):
            log.error(f"Error fetching PR stats for #{pr['number']} in repo {pr['repo_shortname']}:\n{message}")
            return False

        if jsonresp.get("merged"):
            return True

        # checking for the label, using `jsonresp` which has the label information
        if self._has_label(jsonresp, "hacktoberfest-accepted"):
            return True

        # checking approval
        query_url += "/reviews"
        jsonresp2 = await self._fetch_url(query_url, REQUEST_HEADERS)
        if isinstance(jsonresp2, dict):
            # if API request is unsuccessful it will be a dict with the error in 'message'
            log.error(
                f"Error fetching PR reviews for #{pr['number']} in repo {pr['repo_shortname']}:\n"
                f"{jsonresp2['message']}"
            )
            return False
        # if it is successful it will be a list instead of a dict
        if len(jsonresp2) == 0:  # if PR has no reviews
            return False

        # loop through reviews and check for approval
        return any(item.get("status") == "APPROVED" for item in jsonresp2)

    @staticmethod
    def _get_shortname(in_url: str) -> str:
        """
        Extract shortname from https://api.github.com/repos/* URL.

        e.g. "https://api.github.com/repos/python-discord/sir-lancebot"
             |
             V
             "python-discord/sir-lancebot"
        """
        exp = r"https?:\/\/api.github.com\/repos\/([/\-\_\.\w]+)"
        return re.findall(exp, in_url)[0]

    async def _categorize_prs(self, prs: list[dict]) -> tuple:
        """
        Categorize PRs into 'in_review' and 'accepted' and returns as a tuple.

        PRs created less than 14 days ago are 'in_review', PRs that are not
        are 'accepted' (after 14 days review period).

        PRs that are accepted must either be merged, approved, or labelled
        'hacktoberfest-accepted.
        """
        now = datetime.now(tz=UTC)
        oct3 = datetime(CURRENT_YEAR, 10, 3, 23, 59, 59, tzinfo=UTC)
        in_review = []
        accepted = []
        for pr in prs:
            if (pr["created_at"] + timedelta(REVIEW_DAYS)) > now:
                in_review.append(pr)
            elif (pr["created_at"] <= oct3) or await self._is_accepted(pr):
                accepted.append(pr)

        return in_review, accepted

    @staticmethod
    def _build_prs_string(prs: list[tuple], user: str) -> str:
        """
        Builds a discord embed compatible string for a list of PRs.

        Repository name with the link to pull requests authored by 'user' for
        each PR.
        """
        base_url = "https://www.github.com/"
        str_list = []
        repo_list = [pr["repo_shortname"] for pr in prs]
        prs_list = Counter(repo_list).most_common(5)  # get first 5 counted PRs
        more = len(prs) - sum(i[1] for i in prs_list)

        for pr in prs_list:
            # for example: https://www.github.com/python-discord/bot/pulls/octocat
            # will display pull requests authored by octocat.
            # pr[1] is the number of PRs to the repo
            string = f"{pr[1]} to [{pr[0]}]({base_url}{pr[0]}/pulls/{user})"
            str_list.append(string)
        if more:
            str_list.append(f"...and {more} more")

        return "\n".join(str_list)

    @staticmethod
    def _contributionator(n: int) -> str:
        """Return "contribution" or "contributions" based on the value of n."""
        if n == 1:
            return "contribution"
        return "contributions"

    @staticmethod
    def _author_mention_from_context(ctx: commands.Context) -> tuple[str, str]:
        """Return stringified Message author ID and mentionable string from commands.Context."""
        author_id = str(ctx.author.id)
        author_mention = ctx.author.mention

        return author_id, author_mention


async def setup(bot: Bot) -> None:
    """Load the Hacktober Stats Cog."""
    if not Tokens.github:
        log.warning("No GitHub token was provided. The HacktoberStats Cog won't be fully functional.")
    await bot.add_cog(HacktoberStats(bot))

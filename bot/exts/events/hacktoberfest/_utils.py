import logging
import random
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional, Union
from urllib.parse import quote_plus

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES, Tokens

log = logging.getLogger(__name__)

# Constants for `.hacktoberfest issue`
ISSUES_REQUEST_HEADERS = {
    "User-Agent": "Python Discord Hacktoberbot",
    "Accept": "application / vnd.github.v3 + json"
}
if GITHUB_TOKEN := Tokens.github:
    ISSUES_REQUEST_HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

# Constants for `.hacktoberfest stats`
CURRENT_YEAR = datetime.now().year  # Used to construct GH API query
PRS_FOR_SHIRT = 4  # Minimum number of PRs before a shirt is awarded
REVIEW_DAYS = 14  # number of days needed after PR can be mature

STATS_REQUEST_HEADERS = {"User-Agent": "Python Discord Hacktoberbot"}
GITHUB_TOPICS_ACCEPT_HEADER = {"Accept": "application/vnd.github.mercy-preview+json"}

# using repo topics API during preview period requires an accept header
if GITHUB_TOKEN := Tokens.github:
    STATS_REQUEST_HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"
    GITHUB_TOPICS_ACCEPT_HEADER["Authorization"] = f"token {GITHUB_TOKEN}"

GITHUB_NONEXISTENT_USER_MESSAGE = (
    "The listed users cannot be searched either because the users do not exist "
    "or you do not have permission to view the users."
)

URL = (
    "https://api.github.com/search/issues?"  # base url
    "per_page=100"                           # limit results per-page returned by API to 100 (the maximum)
    "&q="                                    # add query parameters
    "is:issue+"                              # is an issue
    "state:open+"                            # that's open
    "label:hacktoberfest+"                   # with the `hacktoberfest` label...
    "language:python"                        # in Python.
)


# Util functions for `.hacktoberfest timeleft`
def in_hacktober() -> bool:
    """Return True if the current time is within Hacktoberfest."""
    _, end, start = load_date()

    now = datetime.utcnow()

    return start <= now <= end


def load_date() -> tuple[datetime, datetime, datetime]:
    """Return of a tuple of the current time and the end and start times of the next October."""
    now = datetime.utcnow()
    year = now.year
    if now.month > 10:
        year += 1
    end = datetime(year, 11, 1, 12)  # November 1st 12:00 (UTC-12:00)
    start = datetime(year, 9, 30, 10)  # September 30th 10:00 (UTC+14:00)
    return now, end, start


# Util functions for `.hacktoberfest stats`
async def get_stats(ctx: commands.Context, github_username: str) -> None:
    """
    Query GitHub's API for PRs created by a GitHub user during the month of October.

    PRs with an 'invalid' or 'spam' label are ignored unless merged or approved.

    PRs have to be in a repository that has a 'hacktoberfest' topic,
    unless the PR is labelled 'hacktoberfest-accepted' for it to count.

    If a valid `github_username` is provided, an embed is generated and posted to the channel.

    Otherwise, a helpful error message is posted.
    """
    async with ctx.typing():
        prs = await get_october_prs(ctx.bot, github_username)

        if prs is None:  # Will be `None` if the user was not found
            await ctx.send(
                embed=discord.Embed(
                    title=random.choice(NEGATIVE_REPLIES),
                    description=f"GitHub user `{github_username}` was not found.",
                    colour=discord.Colour.red()
                )
            )
            return

        if prs:
            stats_embed = await build_stats_embed(ctx.bot, github_username, prs)
            await ctx.send("Here are some stats!", embed=stats_embed)
        else:
            await ctx.send(f"No valid Hacktoberfest PRs found for '{github_username}'")


async def build_stats_embed(bot: Bot, github_username: str, prs: list[dict]) -> discord.Embed:
    """Return a stats embed built from github_username's PRs."""
    logging.info(f"Building Hacktoberfest embed for GitHub user: '{github_username}'")
    in_review, accepted = await categorize_prs(bot, prs)

    n = len(accepted) + len(in_review)  # Total number of PRs
    if n >= PRS_FOR_SHIRT:
        shirtstr = f"**{github_username} is eligible for hacktoberfest swag!**"
    elif (remaining_prs := PRS_FOR_SHIRT - n) == 1:
        shirtstr = f"**{github_username} is 1 PR away from being eligible for hacktoberfest swag!**"
    else:
        shirtstr = f"**{github_username} is {remaining_prs} PRs away from being eligible for hacktoberfest swag!**"

    stats_embed = discord.Embed(
        title=f"{github_username}'s Hacktoberfest",
        color=Colours.purple,
        description=f"{github_username} has made **{n}** valid {contributionator(n)} in October.\n\n{shirtstr}\n\n"
    )

    stats_embed.set_thumbnail(url=f"https://www.github.com/{github_username}.png")
    stats_embed.set_author(
        name="Hacktoberfest",
        url="https://hacktoberfest.digitalocean.com",
        icon_url="https://avatars1.githubusercontent.com/u/35706162?s=200&v=4"
    )

    # This will handle when no PRs in_review or accepted
    review_str = build_prs_string(in_review, github_username) or "None"
    accepted_str = build_prs_string(accepted, github_username) or "None"
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


async def get_october_prs(bot: Bot, github_username: str) -> Optional[list[dict]]:
    """
    Query GitHub's API for PRs created by a GitHub user during the month of October.

    PRs with an 'invalid' or 'spam' label are ignored unless merged or approved.

    PRs have to be in a repository that has a 'hacktoberfest' topic,
    unless the PR is labelled 'hacktoberfest-accepted' for it to count.

    If PRs are found, return a list of dicts with basic PR information.

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

    hacktoberfest_timeframe = f"{CURRENT_YEAR} - 09 - 30T10: 00Z..{CURRENT_YEAR} - 11 - 01T12: 00Z"
    query_params = (
        f"+type:pr"                               # Only get PR if it's:
        f"+is:public"                             # - public
        f"+author:{quote_plus(github_username)}"  # - by the user's github username
        f"+-is:draft"                             # - not a draft
        f"+created:{hacktoberfest_timeframe}"     # - made within hacktoberfest.
        f"&per_page=100"  # Limit results per-page returned from API (100 is the maximum)
    )

    log.debug(f"GitHub query parameters generated: {query_params}")

    # The `params` argument needs to be specified as a string to stop aiohttp percent-encoding
    jsonresp = await fetch_url(bot, base_url, STATS_REQUEST_HEADERS, f"q={query_params}")
    if "message" in jsonresp:
        # One of the parameters is invalid, short circuit for now
        api_message = jsonresp["errors"][0]["message"]

        # Ignore logging non-existent users or users we do not have permission to see
        if api_message == GITHUB_NONEXISTENT_USER_MESSAGE:
            log.debug(f"No GitHub user found named '{github_username}'")
            return
        else:
            log.error(f"GitHub API request for '{github_username}' failed with message: {api_message}")
        return []  # No October PRs were found due to error

    if jsonresp["total_count"] == 0:
        # Short circuit if there aren't any PRs
        log.info(f"No October PRs found for GitHub user: '{github_username}'")
        return []

    logging.info(f"Found {len(jsonresp['items'])} Hacktoberfest PRs for GitHub user: '{github_username}'")
    outlist = []  # List of pr information dicts that will get returned
    hackto_topics = {}  # Cache whether each repo has the appropriate topic (bool values)
    for item in jsonresp["items"]:
        shortname = get_shortname(item["repository_url"])
        itemdict = {
            "repo_url": f"https://www.github.com/{shortname}",
            "repo_shortname": shortname,
            "created_at": datetime.strptime(
                item["created_at"], "%Y-%m-%dT%H:%M:%SZ"
            ),
            "number": item["number"]
        }

        # If the PR has 'invalid' or 'spam' labels, the PR must be
        # either merged or approved for it to be included
        if has_label(item, ["invalid", "spam"]):
            if not await is_accepted(bot, itemdict):
                continue

        # Checking PR's labels for "hacktoberfest-accepted"
        if has_label(item, "hacktoberfest-accepted"):
            outlist.append(itemdict)
            continue

        # No need to query GitHub if repo topics are fetched before already
        if hackto_topics.get(shortname):
            outlist.append(itemdict)
            continue
        # Fetch topics for the PR's repo
        topics_query_url = f"https://api.github.com/repos/{shortname}/topics"
        log.debug(f"Fetching repo topics for {shortname} with url: {topics_query_url}")
        jsonresp2 = await fetch_url(bot, topics_query_url, GITHUB_TOPICS_ACCEPT_HEADER)
        if jsonresp2.get("names") is None:
            log.error(f"Error fetching topics for {shortname}: {jsonresp2['message']}")
            continue  # Assume the repo doesn't have the `hacktoberfest` topic if API request errored

        # PRs that doesn't have 'hacktoberfest-accepted' label
        # must be in repo with 'hacktoberfest' topic
        if "hacktoberfest" in jsonresp2["names"]:
            hackto_topics[shortname] = True  # Cache result in the dict for later use if needed
            outlist.append(itemdict)
    return outlist


async def fetch_url(bot: Bot, url: str, headers: dict, params: Optional[Union[str, dict]] = "") -> dict:
    """Retrieve API JSON response from URL."""
    async with bot.http_session.get(url, headers=headers, params=params) as resp:
        return await resp.json()


def has_label(pr: dict, labels: Union[list[str], str]) -> bool:
    """
    Check if a PR has label 'labels'.

    'labels' can be a string or a list of strings, if it's a list of strings
    it will return true if any of the labels match.
    """
    if not pr.get("labels"):  # If the PR has no labels
        return False
    if isinstance(labels, str) and any(label["name"].casefold() == labels for label in pr["labels"]):
        return True
    for item in labels:
        if any(label["name"].casefold() == item for label in pr["labels"]):
            return True
    return False


async def is_accepted(bot: Bot, pr: dict) -> bool:
    """Check if a PR is merged, approved, or labelled hacktoberfest-accepted."""
    # Check for merge status
    query_url = f"https://api.github.com/repos/{pr['repo_shortname']}/pulls/{pr['number']}"
    jsonresp = await fetch_url(bot, query_url, STATS_REQUEST_HEADERS)

    if message := jsonresp.get("message"):
        log.error(f"Error fetching PR stats for #{pr['number']} in repo {pr['repo_shortname']}:\n{message}")
        return False

    if jsonresp.get("merged"):
        return True

    # Check for the label, using `jsonresp` which has the label information
    if has_label(jsonresp, "hacktoberfest-accepted"):
        return True

    # Check for PR approval
    query_url += "/reviews"
    jsonresp2 = await fetch_url(bot, query_url, STATS_REQUEST_HEADERS)
    if isinstance(jsonresp2, dict):
        # if API request is unsuccessful it will be a dict with the error in 'message'
        log.error(
            f"Error fetching PR reviews for #{pr['number']} in repo {pr['repo_shortname']}:\n"
            f"{jsonresp2['message']}"
        )
        return False
    # If it is successful it will be a list instead of a dict
    if len(jsonresp2) == 0:  # if the PR has no reviews
        return False

    # Loop through reviews and check for approval
    for item in jsonresp2:
        if item.get("status") == "APPROVED":
            return True
    return False


def get_shortname(in_url: str) -> str:
    """
    Extract shortname from https://api.github.com/repos/* URL.

    e.g. "https://api.github.com/repos/python-discord/sir-lancebot"
         |
         V
         "python-discord/sir-lancebot"
    """
    exp = r"https?:\/\/api.github.com\/repos\/([/\-\_\.\w]+)"
    return re.findall(exp, in_url)[0]


async def categorize_prs(bot: Bot, prs: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Categorize PRs into 'in_review' and 'accepted' and returns as a tuple.

    PRs created less than 14 days ago are 'in_review', PRs that are not
    are 'accepted' (after 14 days review period).

    PRs that are accepted must either be merged, approved, or labelled
    'hacktoberfest-accepted'.
    """
    now = datetime.now()
    in_review = []
    accepted = []
    for pr in prs:
        if (pr["created_at"] + timedelta(REVIEW_DAYS)) > now:
            in_review.append(pr)
        elif await is_accepted(bot, pr):
            accepted.append(pr)

    return in_review, accepted


def build_prs_string(prs: list[dict], user: str) -> str:
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
        # For example: https://www.github.com/python-discord/bot/pulls/octocat
        # will display pull requests authored by octocat.
        # pr[1] is the number of PRs to the repo
        string = f"{pr[1]} to [{pr[0]}]({base_url}{pr[0]}/pulls/{user})"
        str_list.append(string)
    if more:
        str_list.append(f"...and {more} more")

    return "\n".join(str_list)


def contributionator(n: int) -> str:
    """Return "contribution" or "contributions" based on the value of n."""
    if n == 1:
        return "contribution"
    else:
        return "contributions"


def author_mention_from_context(ctx: commands.Context) -> tuple[str, str]:
    """Return stringified Message author ID and mentionable string from commands.Context."""
    author_id = str(ctx.author.id)
    author_mention = ctx.author.mention

    return author_id, author_mention


# Util functions for `.hacktoberfest issue`
async def get_issues(ctx: commands.Context, option: str) -> Optional[dict]:
    """Get a list of the python issues with the label 'hacktoberfest' from the Github api."""
    if option == "beginner":
        if (ctx.message.created_at.replace(tzinfo=None) - ctx.cog.cache_timer_beginner).seconds <= 60:
            log.debug("using cache")
            return ctx.cog.cache_beginner
    elif (ctx.message.created_at.replace(tzinfo=None) - ctx.cog.cache_timer_normal).seconds <= 60:
        log.debug("using cache")
        return ctx.cog.cache_normal

    if option == "beginner":
        url = URL + '+label:"good first issue"'
        if ctx.cog.cache_beginner is not None:
            page = random.randint(1, min(1000, ctx.cog.cache_beginner["total_count"]) // 100)
            url += f"&page={page}"
    else:
        url = URL
        if ctx.cog.cache_normal is not None:
            page = random.randint(1, min(1000, ctx.cog.cache_normal["total_count"]) // 100)
            url += f"&page={page}"

    log.debug(f"making api request to url: {url}")
    async with ctx.bot.http_session.get(url, headers=ISSUES_REQUEST_HEADERS) as response:
        if response.status != 200:
            log.error(f"expected 200 status (got {response.status}) by the GitHub api.")
            await ctx.send(
                f"ERROR: expected 200 status (got {response.status}) by the GitHub api.\n"
                f"{await response.text()}"
            )
            return None
        data = await response.json()

        if len(data["items"]) == 0:
            log.error(f"no issues returned by GitHub API, with url: {response.url}")
            await ctx.send(f"ERROR: no issues returned by GitHub API, with url: {response.url}")
            return None

        if option == "beginner":
            ctx.cog.cache_beginner = data
            ctx.cog.cache_timer_beginner = ctx.message.created_at.replace(tzinfo=None)
        else:
            ctx.cog.cache_normal = data
            ctx.cog.cache_timer_normal = ctx.message.created_at.replace(tzinfo=None)

        return data


def format_issues_embed(issue: dict) -> discord.Embed:
    """Format the issue data into a embed."""
    title = issue["title"]
    issue_url = issue["url"].replace("api.", "").replace("/repos/", "/")
    # Issues can have empty bodies, which in that case GitHub doesn't include the key in the API response
    body = issue.get("body") or ''
    labels = [label["name"] for label in issue["labels"]]

    embed = discord.Embed(title=title)
    embed.description = body[:500] + "..." if len(body) > 500 else body
    # Add labels in backticks and joined by a comma
    embed.add_field(name="Labels", value=",".join(map(lambda label: f"`{label}`", labels)))
    embed.url = issue_url
    embed.set_footer(text=issue_url)

    return embed

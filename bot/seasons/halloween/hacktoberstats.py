import json
import logging
import re
import typing
from collections import Counter
from datetime import datetime
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class HacktoberStats:
    def __init__(self, bot):
        self.bot = bot
        self.link_json = Path("bot", "resources", "github_links.json")
        self.linked_accounts = self.load_linked_users()

    @commands.group(
        name='hacktoberstats',
        aliases=('hackstats',),
        invoke_without_command=True
    )
    async def hacktoberstats_group(self, ctx: commands.Context, github_username: str = None):
        """
        If invoked without a subcommand or github_username, get the invoking user's stats if
        they've linked their Discord name to GitHub using .stats link

        If invoked with a github_username, get that user's contributions
        """
        if not github_username:
            author_id, author_mention = HacktoberStats._author_mention_from_context(ctx)

            if str(author_id) in self.linked_accounts.keys():
                github_username = self.linked_accounts[author_id]["github_username"]
                logging.info(f"Getting stats for {author_id} linked GitHub account '{github_username}'")
            else:
                msg = (
                    f"{author_mention}, you have not linked a GitHub account\n\n"
                    f"You can link your GitHub account using:\n```{ctx.prefix}stats link github_username```\n"
                    f"Or query GitHub stats directly using:\n```{ctx.prefix}stats github_username```"
                )
                await ctx.send(msg)
                return

        await self.get_stats(ctx, github_username)

    @hacktoberstats_group.command(name="link")
    async def link_user(self, ctx: commands.Context, github_username: str = None):
        """
        Link the invoking user's Github github_username to their Discord ID

        Linked users are stored as a nested dict:
            {
                Discord_ID: {
                    "github_username": str
                    "date_added": datetime
                }
            }
        """
        author_id, author_mention = HacktoberStats._author_mention_from_context(ctx)
        if github_username:
            if str(author_id) in self.linked_accounts.keys():
                old_username = self.linked_accounts[author_id]["github_username"]
                logging.info(f"{author_id} has changed their github link from '{old_username}' to '{github_username}'")
                await ctx.send(f"{author_mention}, your GitHub username has been updated to: '{github_username}'")
            else:
                logging.info(f"{author_id} has added a github link to '{github_username}'")
                await ctx.send(f"{author_mention}, your GitHub username has been added")

            self.linked_accounts[author_id] = {
                "github_username": github_username,
                "date_added": datetime.now()
            }

            self.save_linked_users()
        else:
            logging.info(f"{author_id} tried to link a GitHub account but didn't provide a username")
            await ctx.send(f"{author_mention}, a GitHub username is required to link your account")

    @hacktoberstats_group.command(name="unlink")
    async def unlink_user(self, ctx: commands.Context):
        """
        Remove the invoking user's account link from the log
        """
        author_id, author_mention = HacktoberStats._author_mention_from_context(ctx)

        stored_user = self.linked_accounts.pop(author_id, None)
        if stored_user:
            await ctx.send(f"{author_mention}, your GitHub profile has been unlinked")
            logging.info(f"{author_id} has unlinked their GitHub account")
        else:
            await ctx.send(f"{author_mention}, you do not currently have a linked GitHub account")
            logging.info(f"{author_id} tried to unlink their GitHub account but no account was linked")

        self.save_linked_users()

    def load_linked_users(self) -> typing.Dict:
        """
        Load list of linked users from local JSON file

        Linked users are stored as a nested dict:
            {
                Discord_ID: {
                    "github_username": str
                    "date_added": datetime
                }
            }
        """
        if self.link_json.exists():
            logging.info(f"Loading linked GitHub accounts from '{self.link_json}'")
            with open(self.link_json, 'r') as fID:
                linked_accounts = json.load(fID)

            logging.info(f"Loaded {len(linked_accounts)} linked GitHub accounts from '{self.link_json}'")
            return linked_accounts
        else:
            logging.info(f"Linked account log: '{self.link_json}' does not exist")
            return {}

    def save_linked_users(self):
        """
        Save list of linked users to local JSON file

        Linked users are stored as a nested dict:
            {
                Discord_ID: {
                    "github_username": str
                    "date_added": datetime
                }
            }
        """
        logging.info(f"Saving linked_accounts to '{self.link_json}'")
        with open(self.link_json, 'w') as fID:
            json.dump(self.linked_accounts, fID, default=str)
        logging.info(f"linked_accounts saved to '{self.link_json}'")

    async def get_stats(self, ctx: commands.Context, github_username: str):
        """
        Query GitHub's API for PRs created by a GitHub user during the month of October that
        do not have an 'invalid' tag

        For example:
            !getstats heavysaturn

        If a valid github_username is provided, an embed is generated and posted to the channel

        Otherwise, post a helpful error message
        """
        async with ctx.typing():
            prs = await self.get_october_prs(github_username)

            if prs:
                stats_embed = self.build_embed(github_username, prs)
                await ctx.send('Here are some stats!', embed=stats_embed)
            else:
                await ctx.send(f"No October GitHub contributions found for '{github_username}'")

    def build_embed(self, github_username: str, prs: typing.List[dict]) -> discord.Embed:
        """
        Return a stats embed built from github_username's PRs
        """
        logging.info(f"Building Hacktoberfest embed for GitHub user: '{github_username}'")
        pr_stats = self._summarize_prs(prs)

        n = pr_stats['n_prs']
        if n >= 5:
            shirtstr = f"**{github_username} has earned a tshirt!**"
        elif n == 4:
            shirtstr = f"**{github_username} is 1 PR away from a tshirt!**"
        else:
            shirtstr = f"**{github_username} is {5 - n} PRs away from a tshirt!**"

        stats_embed = discord.Embed(
            title=f"{github_username}'s Hacktoberfest",
            color=discord.Color(0x9c4af7),
            description=(
                f"{github_username} has made {n} "
                f"{HacktoberStats._contributionator(n)} in "
                f"October\n\n"
                f"{shirtstr}\n\n"
            )
        )

        stats_embed.set_thumbnail(url=f"https://www.github.com/{github_username}.png")
        stats_embed.set_author(
            name="Hacktoberfest",
            url="https://hacktoberfest.digitalocean.com",
            icon_url="https://hacktoberfest.digitalocean.com/assets/logo-hacktoberfest.png"
        )
        stats_embed.add_field(
            name="Top 5 Repositories:",
            value=self._build_top5str(pr_stats)
        )

        logging.info(f"Hacktoberfest PR built for GitHub user '{github_username}'")
        return stats_embed

    @staticmethod
    async def get_october_prs(github_username: str) -> typing.List[dict]:
        """
        Query GitHub's API for PRs created during the month of October by github_username
        that do not have an 'invalid' tag

        If PRs are found, return a list of dicts with basic PR information

        For each PR:
            {
            "repo_url": str
            "repo_shortname": str (e.g. "python-discord/seasonalbot")
            "created_at": datetime.datetime
            }

        Otherwise, return None
        """
        logging.info(f"Generating Hacktoberfest PR query for GitHub user: '{github_username}'")
        base_url = "https://api.github.com/search/issues?q="
        not_label = "invalid"
        action_type = "pr"
        is_query = f"public+author:{github_username}"
        date_range = "2018-10-01..2018-10-31"
        per_page = "300"
        query_url = (
            f"{base_url}"
            f"-label:{not_label}"
            f"+type:{action_type}"
            f"+is:{is_query}"
            f"+created:{date_range}"
            f"&per_page={per_page}"
        )

        headers = {"user-agent": "Discord Python Hactoberbot"}
        async with aiohttp.ClientSession() as session:
            async with session.get(query_url, headers=headers) as resp:
                jsonresp = await resp.json()

        if "message" in jsonresp.keys():
            # One of the parameters is invalid, short circuit for now
            api_message = jsonresp["errors"][0]["message"]
            logging.error(f"GitHub API request for '{github_username}' failed with message: {api_message}")
            return
        else:
            if jsonresp["total_count"] == 0:
                # Short circuit if there aren't any PRs
                logging.info(f"No Hacktoberfest PRs found for GitHub user: '{github_username}'")
                return
            else:
                logging.info(f"Found {len(jsonresp['items'])} Hacktoberfest PRs for GitHub user: '{github_username}'")
                outlist = []
                for item in jsonresp["items"]:
                    shortname = HacktoberStats._get_shortname(item["repository_url"])
                    itemdict = {
                        "repo_url": f"https://www.github.com/{shortname}",
                        "repo_shortname": shortname,
                        "created_at": datetime.strptime(
                            item["created_at"], r"%Y-%m-%dT%H:%M:%SZ"
                        ),
                    }
                    outlist.append(itemdict)
                return outlist

    @staticmethod
    def _get_shortname(in_url: str) -> str:
        """
        Extract shortname from https://api.github.com/repos/* URL

        e.g. "https://api.github.com/repos/python-discord/seasonalbot"
             |
             V
             "python-discord/seasonalbot"
        """
        exp = r"https?:\/\/api.github.com\/repos\/([/\-\_\.\w]+)"
        return re.findall(exp, in_url)[0]

    @staticmethod
    def _summarize_prs(prs: typing.List[dict]) -> typing.Dict:
        """
        Generate statistics from an input list of PR dictionaries, as output by get_october_prs

        Return a dictionary containing:
            {
            "n_prs": int
            "top5": [(repo_shortname, ncontributions), ...]
            }
        """
        contributed_repos = [pr["repo_shortname"] for pr in prs]
        return {"n_prs": len(prs), "top5": Counter(contributed_repos).most_common(5)}

    @staticmethod
    def _build_top5str(stats: typing.List[tuple]) -> str:
        """
        Build a string from the Top 5 contributions that is compatible with a discord.Embed field

        Top 5 contributions should be a list of tuples, as output in the stats dictionary by
        _summarize_prs

        String is of the form:
           n contribution(s) to [shortname](url)
           ...
        """
        baseURL = "https://www.github.com/"
        contributionstrs = []
        for repo in stats['top5']:
            n = repo[1]
            contributionstrs.append(f"{n} {HacktoberStats._contributionator(n)} to [{repo[0]}]({baseURL}{repo[0]})")

        return "\n".join(contributionstrs)

    @staticmethod
    def _contributionator(n: int) -> str:
        """
        Return "contribution" or "contributions" based on the value of n
        """
        if n == 1:
            return "contribution"
        else:
            return "contributions"

    @staticmethod
    def _author_mention_from_context(ctx: commands.Context) -> typing.Tuple:
        """
        Return stringified Message author ID and mentionable string from commands.Context
        """
        author_id = str(ctx.message.author.id)
        author_mention = ctx.message.author.mention

        return author_id, author_mention


def setup(bot):
    bot.add_cog(HacktoberStats(bot))
    log.debug("HacktoberStats cog loaded")

import re
import typing
from collections import Counter
from datetime import datetime

import aiohttp
import discord
from discord.ext import commands


class Stats:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="stats",
        aliases=["getstats", "userstats"],
        brief="Get a user's Hacktoberfest contribution stats",
    )
    async def get_stats(self, ctx, username: str):
        """
        Query GitHub's API for PRs created by a GitHub user during the month of October that
        do not have an 'invalid' tag

        For example:
            !getstats heavysaturn

        If a valid username is provided, an embed is generated and posted to the channel

        Otherwise, post a helpful error message

        The first input argument is treated as the username, any additional inputs are discarded
        """
        prs = await self.get_october_prs(username)

        if prs:
            stats_embed = self.build_embed(username, prs)
            await ctx.send('Here are some stats!', embed=stats_embed)
        else:
            await ctx.send(f"No October GitHub contributions found for '{username}'")

    def build_embed(self, username: str, prs: typing.List[dict]) -> discord.Embed:
        """
        Return a stats embed built from username's PRs
        """
        pr_stats = self._summarize_prs(prs)

        n = pr_stats['n_prs']
        if n >= 5:
            shirtstr = f"**{username} has earned a tshirt!**"
        elif n == 4:
            shirtstr = f"**{username} is 1 PR away from a tshirt!**"
        else:
            shirtstr = f"**{username} is {5 - n} PRs away from a tshirt!**"

        stats_embed = discord.Embed(
            title=f"{username}'s Hacktoberfest",
            color=discord.Color(0x9c4af7),
            description=f"{username} has made {n} {Stats._contributionator(n)} in October\n\n{shirtstr}\n\n"
        )

        stats_embed.set_thumbnail(url=f"https://www.github.com/{username}.png")
        stats_embed.set_author(
            name="Hacktoberfest",
            url="https://hacktoberfest.digitalocean.com",
            icon_url="https://hacktoberfest.digitalocean.com/assets/logo-hacktoberfest.png"
        )
        stats_embed.add_field(
            name="Top 5 Repositories:",
            value=self._build_top5str(pr_stats)
        )

        return stats_embed

    @staticmethod
    async def get_october_prs(username: str) -> typing.List[dict]:
        """
        Query GitHub's API for PRs created during the month of October by username that do
        not have an 'invalid' tag

        If PRs are found, return a list of dicts with basic PR information

        For each PR:
            {
            "repo_url": str
            "repo_shortname": str (e.g. "discord-python/hacktoberbot")
            "created_at": datetime.datetime
            }

        Otherwise, return None
        """
        base_url = "https://api.github.com/search/issues?q="
        not_label = "invalid"
        action_type = "pr"
        is_query = f"public+author:{username}"
        date_range = "2018-10-01..2018-10-31"
        per_page = "300"
        query_url = f"{base_url}-label:{not_label}+type:{action_type}+is:{is_query}+created:{date_range}&per_page={per_page}"

        headers = {"user-agent": "Discord Python Hactoberbot"}
        async with aiohttp.ClientSession() as session:
            async with session.get(query_url, headers=headers) as resp:
                jsonresp = await resp.json()

        if "message" in jsonresp.keys():
            # One of the parameters is invalid, short circuit for now
            # In the future, log: jsonresp["errors"][0]["message"]
            return
        else:
            if jsonresp["total_count"] == 0:
                # Short circuit if there aren't any PRs
                return
            else:
                outlist = []
                for item in jsonresp["items"]:
                    shortname = Stats._get_shortname(item["repository_url"])
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

        e.g. "https://api.github.com/repos/discord-python/hacktoberbot"
             |
             V
             "discord-python/hacktoberbot"
        """
        exp = r"https?:\/\/api.github.com\/repos\/([/\-\w]+)"
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
            contributionstrs.append(f"{n} {Stats._contributionator(n)} to [{repo[0]}]({baseURL}{repo[0]})")

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


def setup(bot):
    bot.add_cog(Stats(bot))

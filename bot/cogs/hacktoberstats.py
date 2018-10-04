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
        self.channelID = (496432022961520650)  # Hardcode #event-hacktoberfest channel ID

    @commands.command(
        name="stats",
        aliases=["getstats", "userstats"],
        brief="Get a user's Hacktoberfest contribution stats",
    )
    async def getstats(self, ctx, *args):
        """
        Query GitHub's API for PRs created by a GitHub user during the month of October that 
        do not have an 'invalid' tag

        For example:
            !getstats heavysaturn

        If a valid username is provided, an embed is generated and posted to the channel

        Otherwise, post a helpful error message

        The first input argument is treated as the username, any additional inputs are discarded
        """
        username = args[0]
        PRs = await self.getoctoberprs(username)

        postchannel = self.bot.get_channel(self.channelID)
        if PRs:
            statsembed = self.buildembed(username, PRs)
            await postchannel.send('Here are some stats!', embed=statsembed)
        else:
            await postchannel.send(f"No October GitHub contributions found for '{username}'")

    def buildembed(self, username: str, PRs: typing.List[dict]) -> discord.Embed:
        """
        Return a stats embed built from username's PRs
        """
        PRstats = self._summarizePRs(PRs)
        
        n = PRstats['nPRs']
        if n >= 5:
            shirtstr = f"**{username} has earned a tshirt!**"
        elif n == 4:
            shirtstr = f"**{username} is 1 PR away from a tshirt!**"
        else:
            shirtstr = f"**{username} is {5 - n} PRs away from a tshirt!**"

        statsembed = discord.Embed(
            title=f"{username}'s Hacktoberfest'",
            color=discord.Color(0x9c4af7),
            description=f"{username} has made {n} {Stats.contributionator(n)} in October\n\n{shirtstr}\n\n"
            )
        statsembed.set_thumbnail(url=f"https://www.github.com/{username}.png")
        statsembed.set_author(
            name="Hacktoberfest",
            url="https://hacktoberfest.digitalocean.com", 
            icon_url="https://hacktoberfest.digitalocean.com/assets/logo-hacktoberfest.png"
            )
        statsembed.add_field(
            name="Top 5 Repositories:", 
            value=self._buildtop5str(stats)
            )
        
        return statsembed

    @staticmethod
    async def getoctoberprs(username: str) -> typing.List[dict]:
        """
        Query GitHub's API for PRs created during the month of October by username that do 
        not have an 'invalid' tag
        
        If PRs are found, return a list of dicts with basic PR information
        
        For each PR:
        
            {
            repo_url: str
            repo_shortname: str (e.g. "discord-python/hacktoberbot")
            created_at: datetime.datetime
            }
        
        Otherwise, return None
        """
        queryURL = f"https://api.github.com/search/issues?q=-label:invalid+type:pr+is:public+author:{username}+created:2018-10-01..2018-10-31&per_page=300"

        headers = {"user-agent": "Discord Python Hactoberbot"}
        async with aiohttp.ClientSession() as session:
            async with session.get(queryURL, headers=headers) as resp:
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
                    shortname = Stats._getURL(item["repository_url"])
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
    def _getURL(inurl: str) -> str:
        """
        Convert GitHub API URL to a regular permalink
        
        e.g. "https://api.github.com/repos/discord-python/hacktoberbot" 
            |
            V
            "https://github.com/discord-python/hacktoberbot"
        """
        exp = r"https?:\/\/api.github.com\/repos\/([/\-\w]+)"
        return re.findall(exp, inurl)[0]

    @staticmethod
    def _summarizePRs(PRs: typing.List[dict]) -> typing.Dict:
        """
        Generate statistics from an input list of PR dictionaries, as output by getoctoberprs
        
        Return a dictionary containing:
            {
            nPRs: int
            top5: [(repo_shortname, ncontributions), ...]
            }
        """
        contributedrepos = [PR["repo_shortname"] for PR in PRs]
        return {"nPRs": len(PRs), "top5": Counter(contributedrepos).most_common(5)}

    @staticmethod
    def _buildtop5str(stats: typing.List[tuple]) -> str:
        """
        Build a string from the Top 5 contributions that is compatible with a discord.Embed field

        Top 5 contributions should be a list of tuples, as output in the stats dictionary by
        _summarizePRs

        String is of the form:
           n contribution(s) to [shortname](url)
           ,,,
        """
        baseURL = "https://www.github.com/"
        contributionstrs = []
        for repo in stats['top5']:
            n = repo[1]
            contributionstrs.append(f"{n} {Stats.contributionator(n)} to [{repo[0]}]({baseURL}{repo[0]})")

        return "\n".join(contributionstrs)

    @staticmethod
    def contributionator(n: int) -> str:
        """
        Return "contribution" or "contributions" based on the value of n
        """

        if n == 1:
            return "contribution"
        else:
            return "contributions"


def setup(bot):
    bot.add_cog(Stats(bot))

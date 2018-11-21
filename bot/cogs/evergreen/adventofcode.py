import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import aiohttp
import discord
from discord.ext import commands

from bot.constants import AdventOfCode as AocConfig
from bot.constants import Colours, Emojis

log = logging.getLogger(__name__)

AOC_SESSION_COOKIE = {"session": AocConfig.session_cookie}


class AdventOfCode:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.about_aoc_filepath = Path("./bot/resources/advent_of_code/about.json")
        self.cached_about_aoc = self._build_about_embed()

        self._base_url = f"https://adventofcode.com/{AocConfig.year}"
        self.private_leaderboard_link = f"{self._base_url}/leaderboard/private/view/{AocConfig.leaderboard_id}"

        self.cached_global_leaderboard = None
        self.cached_private_leaderboard = None

    @commands.group(name="adventofcode", aliases=("aoc",), invoke_without_command=True)
    async def adventofcode_group(self, ctx: commands.Context):
        """
        Advent of Code festivities! Ho Ho Ho!
        """

        await ctx.invoke(self.bot.get_command("help"), "adventofcode")

    @adventofcode_group.command(name="about", aliases=("ab", "info"), brief="Learn about Advent of Code")
    async def about_aoc(self, ctx: commands.Context):
        """
        Respond with an explanation all things Advent of Code
        """

        await ctx.send("", embed=self.cached_about_aoc)

    @adventofcode_group.command(name="join", aliases=("j",), brief="Learn how to join PyDis' private AoC leaderboard")
    async def join_leaderboard(self, ctx: commands.Context):
        """
        Reply with the link to join the PyDis AoC private leaderboard
        """

        info_str = (
            "Head over to https://adventofcode.com/leaderboard/private "
            f"with code `{AocConfig.leaderboard_join_code}` to join the PyDis private leaderboard!"
        )
        await ctx.send(info_str)

    @adventofcode_group.command(
        name="leaderboard",
        aliases=("board", "stats", "lb"),
        brief="Get a snapshot of the PyDis private AoC leaderboard",
    )
    async def aoc_leaderboard(self, ctx: commands.Context, n_disp: int = 10):
        """
        Pull the top n_disp members from the PyDis leaderboard and post an embed

        For readability, n_disp defaults to 10. A maximum value is configured in the
        Advent of Code section of the bot constants. n_disp values greater than this
        limit will default to this maximum and provide feedback to the user.
        """

        async with ctx.typing():
            await self._check_leaderboard_cache(ctx)

            if not self.cached_private_leaderboard:
                # Feedback on issues with leaderboard caching are sent by _check_leaderboard_cache()
                # Short circuit here if there's an issue
                return

            n_disp = await self._check_n_entries(ctx, n_disp)

            # Generate leaderboard table for embed
            members_to_print = self.cached_private_leaderboard.top_n(n_disp)
            table = AocLeaderboard.build_leaderboard_embed(members_to_print)

            # Build embed
            aoc_embed = discord.Embed(colour=Colours.soft_green, timestamp=self.cached_private_leaderboard.last_updated)
            aoc_embed.set_author(name="Advent of Code", url=self.private_leaderboard_link)
            aoc_embed.set_footer(text="Last Updated")

        await ctx.send(
            content=f"Here's the current Top {n_disp}! {Emojis.christmas_tree*3}\n\n{table}", embed=aoc_embed
        )

    @adventofcode_group.command(
        name="global",
        aliases=("globalstats", "globalboard", "gb"),
        brief="Get a snapshot of the global AoC leaderboard",
        hidden=True,
        enabled=False
    )
    async def global_leaderboard(self, ctx: commands.Context, n_disp: int = 10):
        """
        Pull the top n_disp members from the global AoC leaderboard and post an embed

        For readability, n_disp defaults to 10. A maximum value is configured in the
        Advent of Code section of the bot constants. n_disp values greater than this
        limit will default to this maximum and provide feedback to the user.
        """

        async with ctx.typing():
            await self._check_leaderboard_cache(ctx, global_board=True)

            if not self.cached_global_leaderboard:
                # Feedback on issues with leaderboard caching are sent by _check_leaderboard_cache()
                # Short circuit here if there's an issue
                return

            n_disp = await self._check_n_entries(ctx, n_disp)

            # Generate leaderboard table for embed
            members_to_print = self.cached_global_leaderboard.top_n(n_disp)
            table = AocLeaderboard.build_leaderboard_embed(members_to_print)

            # Build embed
            aoc_embed = discord.Embed(colour=Colours.soft_green, timestamp=self.cached_global_leaderboard.last_updated)
            aoc_embed.set_author(name="Advent of Code", url=self._base_url)
            aoc_embed.set_footer(text="Last Updated")

        await ctx.send(
            content=f"Here's the current global Top {n_disp}! {Emojis.christmas_tree*3}\n\n{table}", embed=aoc_embed
        )

    async def _check_leaderboard_cache(self, ctx, global_board: bool = False):
        """
        Check age of current leaderboard & pull a new one if the board is too old

        global_board is a boolean to toggle between the global board and the Pydis private board
        """

        # Toggle between global & private leaderboards
        if global_board:
            log.debug("Checking global leaderboard cache")
            leaderboard_str = "cached_global_leaderboard"
            _shortstr = "global"
        else:
            log.debug("Checking private leaderboard cache")
            leaderboard_str = "cached_private_leaderboard"
            _shortstr = "private"

        leaderboard = getattr(self, leaderboard_str)
        if not leaderboard:
            log.debug(f"No cached {_shortstr} leaderboard found")
            await self._boardgetter(global_board)
        else:
            leaderboard_age = datetime.utcnow() - self.cached_private_leaderboard.last_updated
            age_seconds = leaderboard_age.total_seconds()
            if age_seconds < AocConfig.leaderboard_cache_age_threshold_seconds:
                log.debug(f"Cached {_shortstr} leaderboard age less than threshold ({age_seconds} seconds old)")
            else:
                log.debug(f"Cached {_shortstr} leaderboard age greater than threshold ({age_seconds} seconds old)")
                await self._boardgetter(global_board)

        leaderboard = getattr(self, leaderboard_str)
        if not leaderboard:
            await ctx.send(
                "",
                _error_embed_helper(
                    title=f"Something's gone wrong and there's no cached {_shortstr} leaderboard!",
                    description="Please check in with a staff member.",
                ),
            )

    async def _check_n_entries(self, ctx: commands.Context, n_disp: int) -> int:
        # Check for n > max_entries and n <= 0
        max_entries = AocConfig.leaderboard_max_displayed_members
        author = ctx.message.author
        if not 0 <= n_disp <= max_entries:
            log.debug(
                f"{author.name} ({author.id}) attempted to fetch an invalid number "
                f" of entries from the AoC leaderboard ({n_disp})"
            )
            await ctx.send(
                f":x: {author.mention}, number of entries to display must be a positive "
                f"integer less than or equal to {max_entries}\n\n"
                f"Head to {self.private_leaderboard_link} to view the entire leaderboard"
            )
            n_disp = max_entries

        return n_disp

    def _build_about_embed(self) -> discord.Embed:
        """
        Build and return the informational "About AoC" embed from the resources file
        """

        with self.about_aoc_filepath.open("r") as f:
            embed_fields = json.load(f)

        about_embed = discord.Embed(
            title="https://adventofcode.com/", colour=Colours.soft_green, url="https://adventofcode.com/"
        )
        about_embed.set_author(name="Advent of Code", url="https://discordapp.com")
        for field in embed_fields:
            about_embed.add_field(**field)

        about_embed.set_footer(text=f"Last Updated (UTC): {datetime.utcnow()}")

        return about_embed

    async def _boardgetter(self, global_board: bool):
        """
        Invoke the proper leaderboard getter based on the global_board boolean
        """
        if global_board:
            self.cached_global_leaderboard = await AocLeaderboard.get_global_leaderboard()
        else:
            self.cached_private_leaderboard = await AocLeaderboard.from_url()


class AocMember:
    def __init__(self, name: str, aoc_id: int, stars: int, starboard: list, local_score: int, global_score: int):
        self.name = name
        self.aoc_id = aoc_id
        self.stars = stars
        self.starboard = starboard
        self.local_score = local_score
        self.global_score = global_score
        self.completions = self._completions_from_starboard(self.starboard)

    def __repr__(self):
        return f"<{self.name} ({self.aoc_id}): {self.local_score}>"

    @classmethod
    def member_from_json(cls, injson: dict) -> "AocMember":
        """
        Generate an AocMember from AoC's private leaderboard API JSON

        injson is expected to be the dict contained in:

            AoC_APIjson['members'][<member id>:str]

        Returns an AocMember object
        """

        return cls(
            name=injson["name"] if injson["name"] else "Anonymous User",
            aoc_id=int(injson["id"]),
            stars=injson["stars"],
            starboard=cls._starboard_from_json(injson["completion_day_level"]),
            local_score=injson["local_score"],
            global_score=injson["global_score"],
        )

    @staticmethod
    def _starboard_from_json(injson: dict) -> list:
        """
        Generate starboard from AoC's private leaderboard API JSON

        injson is expected to be the dict contained in:

            AoC_APIjson['members'][<member id>:str]['completion_day_level']

        Returns a list of 25 lists, where each nested list contains a pair of booleans representing
        the code challenge completion status for that day
        """

        # Basic input validation
        if not isinstance(injson, dict):
            raise ValueError

        # Initialize starboard
        starboard = []
        for _i in range(25):
            starboard.append([False, False])

        # Iterate over days, which are the keys of injson (as str)
        for day in injson:
            idx = int(day) - 1
            # If there is a second star, the first star must be completed
            if "2" in injson[day].keys():
                starboard[idx] = [True, True]
            # If the day exists in injson, then at least the first star is completed
            else:
                starboard[idx] = [True, False]

        return starboard

    @staticmethod
    def _completions_from_starboard(starboard: list) -> tuple:
        """
        Return days completed, as a (1 star, 2 star) tuple, from starboard
        """

        completions = [0, 0]
        for day in starboard:
            if day[0]:
                completions[0] += 1
            if day[1]:
                completions[1] += 1

        return tuple(completions)


class AocLeaderboard:
    def __init__(self, members: list, owner_id: int, event_year: int):
        self.members = members
        self._owner_id = owner_id
        self._event_year = event_year
        self.last_updated = datetime.utcnow()

    def top_n(self, n: int = 10) -> dict:
        """
        Return the top n participants on the leaderboard.

        If n is not specified, default to the top 10
        """

        return self.members[:n]

    @staticmethod
    async def json_from_url(
        leaderboard_id: int = AocConfig.leaderboard_id, year: int = AocConfig.year
    ) -> "AocLeaderboard":
        """
        Request the API JSON from Advent of Code for leaderboard_id for the specified year's event

        If no year is input, year defaults to the current year
        """

        api_url = f"https://adventofcode.com/{year}/leaderboard/private/view/{leaderboard_id}.json"

        log.debug("Querying Advent of Code Private Leaderboard API")
        headers = {"user-agent": "PythonDiscord AoC Event Bot"}
        async with aiohttp.ClientSession(cookies=AOC_SESSION_COOKIE, headers=headers) as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    raw_dict = await resp.json()
                else:
                    log.warning(f"Bad response received from AoC ({resp.status}), check session cookie")
                    resp.raise_for_status()

        return raw_dict

    @classmethod
    def from_json(cls, injson: dict) -> "AocLeaderboard":
        """
        Generate an AocLeaderboard object from AoC's private leaderboard API JSON
        """

        return cls(
            members=cls._sorted_members(injson["members"]), owner_id=injson["owner_id"], event_year=injson["event"]
        )

    @classmethod
    async def from_url(cls) -> "AocLeaderboard":
        """
        Helper wrapping of AocLeaderboard.json_from_url and AocLeaderboard.from_json
        """

        api_json = await cls.json_from_url()
        return cls.from_json(api_json)

    @classmethod
    async def get_global_leaderboard(cls) -> "AocLeaderboard":
        """
        Generate an AocLeaderboard from AoC's global leaderboard

        Because there is no API for this, web scraping needs to be used
        """
        raise NotImplementedError

    @staticmethod
    def _sorted_members(injson: dict) -> list:
        """
        Generate a sorted list of AocMember objects from AoC's private leaderboard API JSON

        Output list is sorted based on the AocMember.local_score
        """

        members = [AocMember.member_from_json(injson[member]) for member in injson]
        members.sort(key=lambda x: x.local_score, reverse=True)

        return members

    @staticmethod
    def build_leaderboard_embed(members_to_print: List[AocMember]) -> str:
        """
        Build a text table from members_to_print, a list of AocMember objects

        Returns a string to be used as the content of the bot's leaderboard response
        """

        stargroup = f"{Emojis.star}, {Emojis.star*2}"
        header = f"{' '*3}{'Score'} {'Name':^25} {stargroup:^7}\n{'-'*44}"
        table = ""
        for i, member in enumerate(members_to_print):
            if member.name == "Anonymous User":
                name = f"{member.name} #{member.aoc_id}"
            else:
                name = member.name

            table += (
                f"{i+1:2}) {member.local_score:4} {name:25.25} "
                f"({member.completions[0]:2}, {member.completions[1]:2})\n"
            )
        else:
            table = f"```{header}\n{table}```"

        return table


def _error_embed_helper(title: str, description: str) -> discord.Embed:
    """
    Return a red-colored Embed with the given title and description
    """

    return discord.Embed(title=title, description=description, colour=discord.Colour.red())


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AdventOfCode(bot))
    log.info("Cog loaded: adventofcode")

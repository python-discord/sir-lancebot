import asyncio
import json
import logging
import math
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.ext import commands
from pytz import timezone

from bot.constants import AdventOfCode as AocConfig, Colours, Emojis, Tokens

log = logging.getLogger(__name__)

AOC_REQUEST_HEADER = {"user-agent": "PythonDiscord AoC Event Bot"}
AOC_SESSION_COOKIE = {"session": Tokens.aoc_session_cookie}

EST = timezone("EST")
COUNTDOWN_STEP = 60 * 5


def is_in_advent() -> bool:
    """
    Utility function to check if we are between December 1st
    and December 25th.
    """
    # Run the code from the 1st to the 24th
    return datetime.now(EST).day in range(1, 25) and datetime.now(EST).month == 12


def time_left_to_aoc_midnight() -> Tuple[datetime, timedelta]:
    """
    This calculates the amount of time left until midnight in
    UTC-5 (Advent of Code maintainer timezone).
    """
    # Change all time properties back to 00:00
    todays_midnight = datetime.now(EST).replace(microsecond=0,
                                                second=0,
                                                minute=0,
                                                hour=0)

    # We want tomorrow so add a day on
    tomorrow = todays_midnight + timedelta(days=1)

    # Calculate the timedelta between the current time and midnight
    return tomorrow, tomorrow - datetime.now(EST)


async def countdown_status(bot: commands.Bot):
    """
    Every `COUNTDOWN_STEP` seconds set the playing status of the bot to
    the number of minutes & hours left until the next day's release.
    """
    while is_in_advent():
        _, time_left = time_left_to_aoc_midnight()

        aligned_seconds = int(math.ceil(time_left.seconds / COUNTDOWN_STEP)) * COUNTDOWN_STEP
        hours, minutes = aligned_seconds // 3600, aligned_seconds // 60 % 60

        if aligned_seconds == 0:
            playing = f"right now!"
        elif aligned_seconds == COUNTDOWN_STEP:
            playing = f"in less than {minutes} minutes"
        elif hours == 0:
            playing = f"in {minutes} minutes"
        elif hours == 23:
            playing = f"since {60 - minutes} minutes ago"
        else:
            playing = f"in {hours} hours and {minutes} minutes"

        # Status will look like "Playing in 5 hours and 30 minutes"
        await bot.change_presence(activity=discord.Game(playing))

        # Sleep until next aligned time or a full step if already aligned
        delay = time_left.seconds % COUNTDOWN_STEP or COUNTDOWN_STEP
        await asyncio.sleep(delay)


async def day_countdown(bot: commands.Bot):
    """
    Calculate the number of seconds left until the next day of advent. Once
    we have calculated this we should then sleep that number and when the time
    is reached ping the advent of code role notifying them that the new task is
    ready.
    """
    while is_in_advent():
        tomorrow, time_left = time_left_to_aoc_midnight()

        await asyncio.sleep(time_left.seconds)

        channel = bot.get_channel(AocConfig.channel_id)

        if not channel:
            log.error("Could not find the AoC channel to send notification in")
            break

        await channel.send(f"<@&{AocConfig.role_id}> Good morning! Day {tomorrow.day} is ready to be attempted. "
                           f"View it online now at https://adventofcode.com/{AocConfig.year}/day/{tomorrow.day}"
                           f" (this link could take a few minutes to start working). Good luck!")

        # Wait a couple minutes so that if our sleep didn't sleep enough
        # time we don't end up announcing twice.
        await asyncio.sleep(120)


class AdventOfCode:
    """
    Advent of Code festivities! Ho Ho Ho!
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self._base_url = f"https://adventofcode.com/{AocConfig.year}"
        self.global_leaderboard_url = f"https://adventofcode.com/{AocConfig.year}/leaderboard"
        self.private_leaderboard_url = f"{self._base_url}/leaderboard/private/view/{AocConfig.leaderboard_id}"

        self.about_aoc_filepath = Path("./bot/resources/advent_of_code/about.json")
        self.cached_about_aoc = self._build_about_embed()

        self.cached_global_leaderboard = None
        self.cached_private_leaderboard = None

        self.countdown_task = None
        self.status_task = None

        countdown_coro = day_countdown(self.bot)
        self.countdown_task = asyncio.ensure_future(self.bot.loop.create_task(countdown_coro))

        status_coro = countdown_status(self.bot)
        self.status_task = asyncio.ensure_future(self.bot.loop.create_task(status_coro))

    @commands.group(name="adventofcode", aliases=("aoc",), invoke_without_command=True)
    async def adventofcode_group(self, ctx: commands.Context):
        """
        All of the Advent of Code commands
        """

        await ctx.invoke(self.bot.get_command("help"), "adventofcode")

    @adventofcode_group.command(
        name="subscribe",
        aliases=("sub", "notifications", "notify", "notifs"),
        brief="Notifications for new days"
    )
    async def aoc_subscribe(self, ctx: commands.Context):
        """
        Assign the role for notifications about new days being ready.
        """
        role = ctx.guild.get_role(AocConfig.role_id)
        unsubscribe_command = f"{ctx.prefix}{ctx.command.root_parent} unsubscribe"

        if role not in ctx.author.roles:
            await ctx.author.add_roles(role)
            await ctx.send("Okay! You have been __subscribed__ to notifications about new Advent of Code tasks. "
                           f"You can run `{unsubscribe_command}` to disable them again for you.")
        else:
            await ctx.send("Hey, you already are receiving notifications about new Advent of Code tasks. "
                           f"If you don't want them any more, run `{unsubscribe_command}` instead.")

    @adventofcode_group.command(name="unsubscribe", aliases=("unsub",), brief="Notifications for new days")
    async def aoc_unsubscribe(self, ctx: commands.Context):
        """
        Remove the role for notifications about new days being ready.
        """
        role = ctx.guild.get_role(AocConfig.role_id)

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send("Okay! You have been __unsubscribed__ from notifications about new Advent of Code tasks.")
        else:
            await ctx.send("Hey, you don't even get any notifications about new Advent of Code tasks currently anyway.")

    @adventofcode_group.command(name="countdown", aliases=("count", "c"), brief="Return time left until next day")
    async def aoc_countdown(self, ctx: commands.Context):
        """
        Return time left until next day
        """
        if not is_in_advent():
            datetime_now = datetime.now(EST)
            december_first = datetime(datetime_now.year + 1, 12, 1, tzinfo=EST)
            delta = december_first - datetime_now
            await ctx.send(f"The Advent of Code event is not currently running. "
                           f"The next event will start in {delta.days} days.")
            return

        tomorrow, time_left = time_left_to_aoc_midnight()

        hours, minutes = time_left.seconds // 3600, time_left.seconds // 60 % 60

        await ctx.send(f"There are {hours} hours and {minutes} minutes left until day {tomorrow.day}.")

    @adventofcode_group.command(name="about", aliases=("ab", "info"), brief="Learn about Advent of Code")
    async def about_aoc(self, ctx: commands.Context):
        """
        Respond with an explanation of all things Advent of Code
        """

        await ctx.send("", embed=self.cached_about_aoc)

    @adventofcode_group.command(name="join", aliases=("j",), brief="Learn how to join PyDis' private AoC leaderboard")
    async def join_leaderboard(self, ctx: commands.Context):
        """
        DM the user the information for joining the PyDis AoC private leaderboard
        """

        author = ctx.message.author
        log.info(f"{author.name} ({author.id}) has requested the PyDis AoC leaderboard code")

        info_str = (
            "Head over to https://adventofcode.com/leaderboard/private "
            f"with code `{AocConfig.leaderboard_join_code}` to join the PyDis private leaderboard!"
        )
        try:
            await author.send(info_str)
        except discord.errors.Forbidden:
            log.debug(f"{author.name} ({author.id}) has disabled DMs from server members")
            await ctx.send(f":x: {author.mention}, please (temporarily) enable DMs to receive the join code")

    @adventofcode_group.command(
        name="leaderboard",
        aliases=("board", "lb"),
        brief="Get a snapshot of the PyDis private AoC leaderboard",
    )
    async def aoc_leaderboard(self, ctx: commands.Context, number_of_people_to_display: int = 10):
        """
        Pull the top number_of_people_to_display members from the PyDis leaderboard and post an embed

        For readability, number_of_people_to_display defaults to 10. A maximum value is configured in the
        Advent of Code section of the bot constants. number_of_people_to_display values greater than this
        limit will default to this maximum and provide feedback to the user.
        """

        async with ctx.typing():
            await self._check_leaderboard_cache(ctx)

            if not self.cached_private_leaderboard:
                # Feedback on issues with leaderboard caching are sent by _check_leaderboard_cache()
                # Short circuit here if there's an issue
                return

            number_of_people_to_display = await self._check_n_entries(ctx, number_of_people_to_display)

            # Generate leaderboard table for embed
            members_to_print = self.cached_private_leaderboard.top_n(number_of_people_to_display)
            table = AocPrivateLeaderboard.build_leaderboard_embed(members_to_print)

            # Build embed
            aoc_embed = discord.Embed(
                description=f"Total members: {len(self.cached_private_leaderboard.members)}",
                colour=Colours.soft_green,
                timestamp=self.cached_private_leaderboard.last_updated
            )
            aoc_embed.set_author(name="Advent of Code", url=self.private_leaderboard_url)
            aoc_embed.set_footer(text="Last Updated")

        await ctx.send(
            content=f"Here's the current Top {number_of_people_to_display}! {Emojis.christmas_tree*3}\n\n{table}",
            embed=aoc_embed,
        )

    @adventofcode_group.command(
        name="stats",
        aliases=("dailystats", "ds"),
        brief="Get daily statistics for the PyDis private leaderboard"
    )
    async def private_leaderboard_daily_stats(self, ctx: commands.Context):
        """
        Respond with a table of the daily completion statistics for the PyDis private leaderboard

        Embed will display the total members and the number of users who have completed each day's puzzle
        """

        async with ctx.typing():
            await self._check_leaderboard_cache(ctx)

            if not self.cached_private_leaderboard:
                # Feedback on issues with leaderboard caching are sent by _check_leaderboard_cache()
                # Short circuit here if there's an issue
                return

            # Build ASCII table
            total_members = len(self.cached_private_leaderboard.members)
            _star = Emojis.star
            header = f"{'Day':4}{_star:^8}{_star*2:^4}{'% ' + _star:^8}{'% ' + _star*2:^4}\n{'='*35}"
            table = ""
            for day, completions in enumerate(self.cached_private_leaderboard.daily_completion_summary):
                per_one_star = f"{(completions[0]/total_members)*100:.2f}"
                per_two_star = f"{(completions[1]/total_members)*100:.2f}"

                table += f"{day+1:3}){completions[0]:^8}{completions[1]:^6}{per_one_star:^10}{per_two_star:^6}\n"

            table = f"```\n{header}\n{table}```"

            # Build embed
            daily_stats_embed = discord.Embed(
                colour=Colours.soft_green, timestamp=self.cached_private_leaderboard.last_updated
            )
            daily_stats_embed.set_author(name="Advent of Code", url=self._base_url)
            daily_stats_embed.set_footer(text="Last Updated")

            await ctx.send(
                content=f"Here's the current daily statistics!\n\n{table}", embed=daily_stats_embed
            )

    @adventofcode_group.command(
        name="global",
        aliases=("globalboard", "gb"),
        brief="Get a snapshot of the global AoC leaderboard",
    )
    async def global_leaderboard(self, ctx: commands.Context, number_of_people_to_display: int = 10):
        """
        Pull the top number_of_people_to_display members from the global AoC leaderboard and post an embed

        For readability, number_of_people_to_display defaults to 10. A maximum value is configured in the
        Advent of Code section of the bot constants. number_of_people_to_display values greater than this
        limit will default to this maximum and provide feedback to the user.
        """

        async with ctx.typing():
            await self._check_leaderboard_cache(ctx, global_board=True)

            if not self.cached_global_leaderboard:
                # Feedback on issues with leaderboard caching are sent by _check_leaderboard_cache()
                # Short circuit here if there's an issue
                return

            number_of_people_to_display = await self._check_n_entries(ctx, number_of_people_to_display)

            # Generate leaderboard table for embed
            members_to_print = self.cached_global_leaderboard.top_n(number_of_people_to_display)
            table = AocGlobalLeaderboard.build_leaderboard_embed(members_to_print)

            # Build embed
            aoc_embed = discord.Embed(colour=Colours.soft_green, timestamp=self.cached_global_leaderboard.last_updated)
            aoc_embed.set_author(name="Advent of Code", url=self._base_url)
            aoc_embed.set_footer(text="Last Updated")

        await ctx.send(
            content=f"Here's the current global Top {number_of_people_to_display}! {Emojis.christmas_tree*3}\n\n{table}",  # noqa
            embed=aoc_embed,
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
            leaderboard_age = datetime.utcnow() - leaderboard.last_updated
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
                embed=_error_embed_helper(
                    title=f"Something's gone wrong and there's no cached {_shortstr} leaderboard!",
                    description="Please check in with a staff member.",
                ),
            )

    async def _check_n_entries(self, ctx: commands.Context, number_of_people_to_display: int) -> int:
        # Check for n > max_entries and n <= 0
        max_entries = AocConfig.leaderboard_max_displayed_members
        author = ctx.message.author
        if not 0 <= number_of_people_to_display <= max_entries:
            log.debug(
                f"{author.name} ({author.id}) attempted to fetch an invalid number "
                f" of entries from the AoC leaderboard ({number_of_people_to_display})"
            )
            await ctx.send(
                f":x: {author.mention}, number of entries to display must be a positive "
                f"integer less than or equal to {max_entries}\n\n"
                f"Head to {self.private_leaderboard_url} to view the entire leaderboard"
            )
            number_of_people_to_display = max_entries

        return number_of_people_to_display

    def _build_about_embed(self) -> discord.Embed:
        """
        Build and return the informational "About AoC" embed from the resources file
        """

        with self.about_aoc_filepath.open("r") as f:
            embed_fields = json.load(f)

        about_embed = discord.Embed(title=self._base_url, colour=Colours.soft_green, url=self._base_url)
        about_embed.set_author(name="Advent of Code", url=self._base_url)
        for field in embed_fields:
            about_embed.add_field(**field)

        about_embed.set_footer(text=f"Last Updated (UTC): {datetime.utcnow()}")

        return about_embed

    async def _boardgetter(self, global_board: bool):
        """
        Invoke the proper leaderboard getter based on the global_board boolean
        """
        if global_board:
            self.cached_global_leaderboard = await AocGlobalLeaderboard.from_url()
        else:
            self.cached_private_leaderboard = await AocPrivateLeaderboard.from_url()


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


class AocPrivateLeaderboard:
    def __init__(self, members: list, owner_id: int, event_year: int):
        self.members = members
        self._owner_id = owner_id
        self._event_year = event_year
        self.last_updated = datetime.utcnow()

        self.daily_completion_summary = self.calculate_daily_completion()

    def top_n(self, n: int = 10) -> dict:
        """
        Return the top n participants on the leaderboard.

        If n is not specified, default to the top 10
        """

        return self.members[:n]

    def calculate_daily_completion(self) -> List[tuple]:
        """
        Calculate member completion rates by day

        Return a list of tuples for each day containing the number of users who completed each part
        of the challenge
        """

        daily_member_completions = []
        for day in range(25):
            one_star_count = 0
            two_star_count = 0
            for member in self.members:
                if member.starboard[day][1]:
                    one_star_count += 1
                    two_star_count += 1
                elif member.starboard[day][0]:
                    one_star_count += 1
            else:
                daily_member_completions.append((one_star_count, two_star_count))

        return(daily_member_completions)

    @staticmethod
    async def json_from_url(
        leaderboard_id: int = AocConfig.leaderboard_id, year: int = AocConfig.year
    ) -> "AocPrivateLeaderboard":
        """
        Request the API JSON from Advent of Code for leaderboard_id for the specified year's event

        If no year is input, year defaults to the current year
        """

        api_url = f"https://adventofcode.com/{year}/leaderboard/private/view/{leaderboard_id}.json"

        log.debug("Querying Advent of Code Private Leaderboard API")
        async with aiohttp.ClientSession(cookies=AOC_SESSION_COOKIE, headers=AOC_REQUEST_HEADER) as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    raw_dict = await resp.json()
                else:
                    log.warning(f"Bad response received from AoC ({resp.status}), check session cookie")
                    resp.raise_for_status()

        return raw_dict

    @classmethod
    def from_json(cls, injson: dict) -> "AocPrivateLeaderboard":
        """
        Generate an AocPrivateLeaderboard object from AoC's private leaderboard API JSON
        """

        return cls(
            members=cls._sorted_members(injson["members"]), owner_id=injson["owner_id"], event_year=injson["event"]
        )

    @classmethod
    async def from_url(cls) -> "AocPrivateLeaderboard":
        """
        Helper wrapping of AocPrivateLeaderboard.json_from_url and AocPrivateLeaderboard.from_json
        """

        api_json = await cls.json_from_url()
        return cls.from_json(api_json)

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


class AocGlobalLeaderboard:
    def __init__(self, members: List[tuple]):
        self.members = members
        self.last_updated = datetime.utcnow()

    def top_n(self, n: int = 10) -> dict:
        """
        Return the top n participants on the leaderboard.

        If n is not specified, default to the top 10
        """

        return self.members[:n]

    @classmethod
    async def from_url(cls) -> "AocGlobalLeaderboard":
        """
        Generate an list of tuples for the entries on AoC's global leaderboard

        Because there is no API for this, web scraping needs to be used
        """

        aoc_url = f"https://adventofcode.com/{AocConfig.year}/leaderboard"

        async with aiohttp.ClientSession(headers=AOC_REQUEST_HEADER) as session:
            async with session.get(aoc_url) as resp:
                if resp.status == 200:
                    raw_html = await resp.text()
                else:
                    log.warning(f"Bad response received from AoC ({resp.status}), check session cookie")
                    resp.raise_for_status()

        soup = BeautifulSoup(raw_html, "html.parser")
        ele = soup.find_all("div", class_="leaderboard-entry")

        exp = r"(?:[ ]{,2}(\d+)\))?[ ]+(\d+)\s+([\w\(\)\#\@\-\d ]+)"

        lb_list = []
        for entry in ele:
            # Strip off the AoC++ decorator
            raw_str = entry.text.replace("(AoC++)", "").rstrip()

            # Use a regex to extract the info from the string to unify formatting
            # Group 1: Rank
            # Group 2: Global Score
            # Group 3: Member string
            r = re.match(exp, raw_str)

            rank = int(r.group(1)) if r.group(1) else None
            global_score = int(r.group(2))

            member = r.group(3)
            if member.lower().startswith("(anonymous"):
                # Normalize anonymous user string by stripping () and title casing
                member = re.sub(r"[\(\)]", "", member).title()

            lb_list.append((rank, global_score, member))

        return cls(lb_list)

    @staticmethod
    def build_leaderboard_embed(members_to_print: List[tuple]) -> str:
        """
        Build a text table from members_to_print, a list of tuples

        Returns a string to be used as the content of the bot's leaderboard response
        """

        header = f"{' '*4}{'Score'} {'Name':^25}\n{'-'*36}"
        table = ""
        for member in members_to_print:
            # In the event of a tie, rank is None
            if member[0]:
                rank = f"{member[0]:3})"
            else:
                rank = f"{' ':4}"
            table += f"{rank} {member[1]:4} {member[2]:25.25}\n"
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

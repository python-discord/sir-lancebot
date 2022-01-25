import asyncio
import collections
import datetime
import json
import logging
import math
import operator
from typing import Any, Optional

import aiohttp
import arrow
import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import AdventOfCode, Channels, Colours
from bot.exts.events.advent_of_code import _caches

log = logging.getLogger(__name__)

PASTE_URL = "https://paste.pythondiscord.com/documents"
RAW_PASTE_URL_TEMPLATE = "https://paste.pythondiscord.com/raw/{key}"

# Base API URL for Advent of Code Private Leaderboards
AOC_API_URL = "https://adventofcode.com/{year}/leaderboard/private/view/{leaderboard_id}.json"
AOC_REQUEST_HEADER = {"user-agent": "PythonDiscord AoC Event Bot"}

# Leaderboard Line Template
AOC_TABLE_TEMPLATE = "{rank: >4} | {name:25.25} | {score: >5} | {stars}"
HEADER = AOC_TABLE_TEMPLATE.format(rank="", name="Name", score="Score", stars="⭐, ⭐⭐")
HEADER = f"{HEADER}\n{'-' * (len(HEADER) + 2)}"
HEADER_LINES = len(HEADER.splitlines())
TOP_LEADERBOARD_LINES = HEADER_LINES + AdventOfCode.leaderboard_displayed_members

# Keys that need to be set for a cached leaderboard
REQUIRED_CACHE_KEYS = (
    "full_leaderboard",
    "top_leaderboard",
    "full_leaderboard_url",
    "leaderboard_fetched_at",
    "number_of_participants",
    "daily_stats",
)

AOC_EMBED_THUMBNAIL = (
    "https://raw.githubusercontent.com/python-discord"
    "/branding/main/seasonal/christmas/server_icons/festive_256.gif"
)

# Create an easy constant for the EST timezone
EST = "America/New_York"

# Step size for the challenge countdown status
COUNTDOWN_STEP = 60 * 5

# Create namedtuple that combines a participant's name and their completion
# time for a specific star. We're going to use this later to order the results
# for each star to compute the rank score.
StarResult = collections.namedtuple("StarResult", "member_id completion_time")


class UnexpectedRedirect(aiohttp.ClientError):
    """Raised when an unexpected redirect was detected."""


class UnexpectedResponseStatus(aiohttp.ClientError):
    """Raised when an unexpected redirect was detected."""


class FetchingLeaderboardFailedError(Exception):
    """Raised when one or more leaderboards could not be fetched at all."""


def _format_leaderboard_line(rank: int, data: dict[str, Any], *, is_author: bool) -> str:
    """
    Build a string representing a line of the leaderboard.

    Parameters:
        rank:
            Rank in the leaderboard of this entry.

        data:
            Mapping with entry information.

    Keyword arguments:
        is_author:
            Whether to address the name displayed in the returned line
            personally.

    Returns:
        A formatted line for the leaderboard.
    """
    return AOC_TABLE_TEMPLATE.format(
        rank=rank,
        name=data['name'] if not is_author else f"(You) {data['name']}",
        score=str(data['score']),
        stars=f"({data['star_1']}, {data['star_2']})"
    )


def leaderboard_sorting_function(entry: tuple[str, dict]) -> tuple[int, int]:
    """
    Provide a sorting value for our leaderboard.

    The leaderboard is sorted primarily on the score someone has received and
    secondary on the number of stars someone has completed.
    """
    result = entry[1]
    return result["score"], result["star_2"] + result["star_1"]


def _parse_raw_leaderboard_data(raw_leaderboard_data: dict) -> dict:
    """
    Parse the leaderboard data received from the AoC website.

    The data we receive from AoC is structured by member, not by day/star. This
    means that we need to "transpose" the data to a per star structure in order
    to calculate the rank scores each individual should get.

    As we need our data both "per participant" as well as "per day", we return
    the parsed and analyzed data in both formats.
    """
    # We need to get an aggregate of completion times for each star of each day,
    # instead of per participant to compute the rank scores. This dictionary will
    # provide such a transposed dataset.
    star_results = collections.defaultdict(list)

    # As we're already iterating over the participants, we can record the number of
    # first stars and second stars they've achieved right here and now. This means
    # we won't have to iterate over the participants again later.
    leaderboard = {}

    # The data we get from the AoC website is structured by member, not by day/star,
    # which means we need to iterate over the members to transpose the data to a per
    # star view. We need that per star view to compute rank scores per star.
    per_day_star_stats = collections.defaultdict(list)
    for member in raw_leaderboard_data.values():
        name = member["name"] if member["name"] else f"Anonymous #{member['id']}"
        member_id = member["id"]
        leaderboard[member_id] = {"name": name, "score": 0, "star_1": 0, "star_2": 0}

        # Iterate over all days for this participant
        for day, stars in member["completion_day_level"].items():
            # Iterate over the complete stars for this day for this participant
            for star, data in stars.items():
                # Record completion of this star for this individual
                leaderboard[member_id][f"star_{star}"] += 1

                # Record completion datetime for this participant for this day/star
                completion_time = datetime.datetime.fromtimestamp(int(data["get_star_ts"]))
                star_results[(day, star)].append(
                    StarResult(member_id=member_id, completion_time=completion_time)
                )
                per_day_star_stats[f"{day}-{star}"].append(
                    {'completion_time': int(data["get_star_ts"]), 'member_name': name}
                )
    for key in per_day_star_stats:
        per_day_star_stats[key] = sorted(per_day_star_stats[key], key=operator.itemgetter('completion_time'))

    # Now that we have a transposed dataset that holds the completion time of all
    # participants per star, we can compute the rank-based scores each participant
    # should get for that star.
    max_score = len(leaderboard)
    for (day, _star), results in star_results.items():
        # If this day should not count in the ranking, skip it.
        if day in AdventOfCode.ignored_days:
            continue

        sorted_result = sorted(results, key=operator.attrgetter("completion_time"))
        for rank, star_result in enumerate(sorted_result):
            leaderboard[star_result.member_id]["score"] += max_score - rank

    # Since dictionaries now retain insertion order, let's use that
    sorted_leaderboard = dict(
        sorted(leaderboard.items(), key=leaderboard_sorting_function, reverse=True)
    )

    # Create summary stats for the stars completed for each day of the event.
    daily_stats = {}
    for day in range(1, 26):
        day = str(day)
        star_one = len(star_results.get((day, "1"), []))
        star_two = len(star_results.get((day, "2"), []))
        # By using a dictionary instead of namedtuple here, we can serialize
        # this data to JSON in order to cache it in Redis.
        daily_stats[day] = {"star_one": star_one, "star_two": star_two}

    return {"daily_stats": daily_stats, "leaderboard": sorted_leaderboard, 'per_day_and_star': per_day_star_stats}


def _format_leaderboard(leaderboard: dict[str, dict], self_placement_name: str = None) -> str:
    """Format the leaderboard using the AOC_TABLE_TEMPLATE."""
    leaderboard_lines = [HEADER]
    self_placement_exists = False
    for rank, data in enumerate(leaderboard.values(), start=1):
        if self_placement_name and data["name"].lower() == self_placement_name.lower():
            leaderboard_lines.insert(
                1,
                AOC_TABLE_TEMPLATE.format(
                    rank=rank,
                    name=f"(You) {data['name']}",
                    score=str(data["score"]),
                    stars=f"({data['star_1']}, {data['star_2']})"
                )
            )
            self_placement_exists = True
            continue
        leaderboard_lines.append(
            AOC_TABLE_TEMPLATE.format(
                rank=rank,
                name=data["name"],
                score=str(data["score"]),
                stars=f"({data['star_1']}, {data['star_2']})"
            )
        )
    if self_placement_name and not self_placement_exists:
        raise commands.BadArgument(
            "Sorry, your profile does not exist in this leaderboard."
            "\n\n"
            "To join our leaderboard, run the command `.aoc join`."
            " If you've joined recently, please wait up to 30 minutes for our leaderboard to refresh."
        )
    return "\n".join(leaderboard_lines)


async def _leaderboard_request(url: str, board: str, cookies: dict) -> dict[str, Any]:
    """Make a leaderboard request using the specified session cookie."""
    async with aiohttp.request("GET", url, headers=AOC_REQUEST_HEADER, cookies=cookies) as resp:
        # The Advent of Code website redirects silently with a 200 response if a
        # session cookie has expired, is invalid, or was not provided.
        if str(resp.url) != url:
            log.error(f"Fetching leaderboard `{board}` failed! Check the session cookie.")
            raise UnexpectedRedirect(f"redirected unexpectedly to {resp.url} for board `{board}`")

        # Every status other than `200` is unexpected, not only 400+
        if not resp.status == 200:
            log.error(f"Unexpected response `{resp.status}` while fetching leaderboard `{board}`")
            raise UnexpectedResponseStatus(f"status `{resp.status}`")

        return await resp.json()


async def _fetch_leaderboard_data() -> dict[str, Any]:
    """Fetch data for all leaderboards and return a pooled result."""
    year = AdventOfCode.year

    # We'll make our requests one at a time to not flood the AoC website with
    # up to six simultaneous requests. This may take a little longer, but it
    # does avoid putting unnecessary stress on the Advent of Code website.

    # Container to store the raw data of each leaderboard
    participants = {}
    for leaderboard in AdventOfCode.leaderboards.values():
        leaderboard_url = AOC_API_URL.format(year=year, leaderboard_id=leaderboard.id)

        # Two attempts, one with the original session cookie and one with the fallback session
        for attempt in range(1, 3):
            log.debug(f"Attempting to fetch leaderboard `{leaderboard.id}` ({attempt}/2)")
            cookies = {"session": leaderboard.session}
            try:
                raw_data = await _leaderboard_request(leaderboard_url, leaderboard.id, cookies)
            except UnexpectedRedirect:
                if cookies["session"] == AdventOfCode.fallback_session:
                    log.error("It seems like the fallback cookie has expired!")
                    raise FetchingLeaderboardFailedError from None

                # If we're here, it means that the original session did not
                # work. Let's fall back to the fallback session.
                leaderboard.use_fallback_session = True
                continue
            except aiohttp.ClientError:
                # Don't retry, something unexpected is wrong and it may not be the session.
                raise FetchingLeaderboardFailedError from None
            else:
                # Get the participants and store their current count.
                board_participants = raw_data["members"]
                await _caches.leaderboard_counts.set(leaderboard.id, len(board_participants))
                participants.update(board_participants)
                break
        else:
            log.error(f"reached 'unreachable' state while fetching board `{leaderboard.id}`.")
            raise FetchingLeaderboardFailedError

    log.info(f"Fetched leaderboard information for {len(participants)} participants")
    return participants


async def _upload_leaderboard(leaderboard: str) -> str:
    """Upload the full leaderboard to our paste service and return the URL."""
    async with aiohttp.request("POST", PASTE_URL, data=leaderboard) as resp:
        try:
            resp_json = await resp.json()
        except Exception:
            log.exception("Failed to upload full leaderboard to paste service")
            return ""

    if "key" in resp_json:
        return RAW_PASTE_URL_TEMPLATE.format(key=resp_json["key"])

    log.error(f"Unexpected response from paste service while uploading leaderboard {resp_json}")
    return ""


def _get_top_leaderboard(full_leaderboard: str) -> str:
    """Get the leaderboard up to the maximum specified entries."""
    return "\n".join(full_leaderboard.splitlines()[:TOP_LEADERBOARD_LINES])


@_caches.leaderboard_cache.atomic_transaction
async def fetch_leaderboard(invalidate_cache: bool = False, self_placement_name: str = None) -> dict:
    """
    Get the current Python Discord combined leaderboard.

    The leaderboard is cached and only fetched from the API if the current data
    is older than the lifetime set in the constants. To prevent multiple calls
    to this function fetching new leaderboard information in case of a cache
    miss, this function is locked to one call at a time using a decorator.
    """
    cached_leaderboard = await _caches.leaderboard_cache.to_dict()
    # Check if the cached leaderboard contains everything we expect it to. If it
    # does not, this probably means the cache has not been created yet or has
    # expired in Redis. This check also accounts for a malformed cache.
    if invalidate_cache or any(key not in cached_leaderboard for key in REQUIRED_CACHE_KEYS):
        log.info("No leaderboard cache available, fetching leaderboards...")
        # Fetch the raw data
        raw_leaderboard_data = await _fetch_leaderboard_data()

        # Parse it to extract "per star, per day" data and participant scores
        parsed_leaderboard_data = _parse_raw_leaderboard_data(raw_leaderboard_data)

        leaderboard = parsed_leaderboard_data["leaderboard"]
        number_of_participants = len(leaderboard)
        formatted_leaderboard = _format_leaderboard(leaderboard)
        full_leaderboard_url = await _upload_leaderboard(formatted_leaderboard)
        leaderboard_fetched_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cached_leaderboard = {
            "placement_leaderboard": json.dumps(raw_leaderboard_data),
            "full_leaderboard": formatted_leaderboard,
            "top_leaderboard": _get_top_leaderboard(formatted_leaderboard),
            "full_leaderboard_url": full_leaderboard_url,
            "leaderboard_fetched_at": leaderboard_fetched_at,
            "number_of_participants": number_of_participants,
            "daily_stats": json.dumps(parsed_leaderboard_data["daily_stats"]),
            "leaderboard_per_day_and_star": json.dumps(parsed_leaderboard_data["per_day_and_star"])
        }

        # Store the new values in Redis
        await _caches.leaderboard_cache.update(cached_leaderboard)

        # Set an expiry on the leaderboard RedisCache
        with await _caches.leaderboard_cache._get_pool_connection() as connection:
            await connection.expire(
                _caches.leaderboard_cache.namespace,
                AdventOfCode.leaderboard_cache_expiry_seconds
            )
    if self_placement_name:
        formatted_placement_leaderboard = _parse_raw_leaderboard_data(
            json.loads(cached_leaderboard["placement_leaderboard"])
        )["leaderboard"]
        cached_leaderboard["placement_leaderboard"] = _get_top_leaderboard(
            _format_leaderboard(formatted_placement_leaderboard, self_placement_name=self_placement_name)
        )
    return cached_leaderboard


def get_summary_embed(leaderboard: dict) -> discord.Embed:
    """Get an embed with the current summary stats of the leaderboard."""
    leaderboard_url = leaderboard["full_leaderboard_url"]
    refresh_minutes = AdventOfCode.leaderboard_cache_expiry_seconds // 60
    refreshed_unix = int(datetime.datetime.fromisoformat(leaderboard["leaderboard_fetched_at"]).timestamp())

    aoc_embed = discord.Embed(colour=Colours.soft_green)

    aoc_embed.description = (
        f"The leaderboard is refreshed every {refresh_minutes} minutes.\n"
        f"Last Updated: <t:{refreshed_unix}:t>"
    )
    aoc_embed.add_field(
        name="Number of Participants",
        value=leaderboard["number_of_participants"],
        inline=True,
    )
    if leaderboard_url:
        aoc_embed.add_field(
            name="Full Leaderboard",
            value=f"[Python Discord Leaderboard]({leaderboard_url})",
            inline=True,
        )
    aoc_embed.set_author(name="Advent of Code", url=leaderboard_url)
    aoc_embed.set_thumbnail(url=AOC_EMBED_THUMBNAIL)

    return aoc_embed


async def get_public_join_code(author: discord.Member) -> Optional[str]:
    """
    Get the join code for one of the non-staff leaderboards.

    If a user has previously requested a join code and their assigned board
    hasn't filled up yet, we'll return the same join code to prevent them from
    getting join codes for multiple boards.
    """
    # Make sure to fetch new leaderboard information if the cache is older than
    # 30 minutes. While this still means that there could be a discrepancy
    # between the current leaderboard state and the numbers we have here, this
    # should work fairly well given the buffer of slots that we have.
    await fetch_leaderboard()
    previously_assigned_board = await _caches.assigned_leaderboard.get(author.id)
    current_board_counts = await _caches.leaderboard_counts.to_dict()

    # Remove the staff board from the current board counts as it should be ignored.
    current_board_counts.pop(AdventOfCode.staff_leaderboard_id, None)

    # If this user has already received a join code, we'll give them the
    # exact same one to prevent them from joining multiple boards and taking
    # up multiple slots.
    if previously_assigned_board:
        # Check if their previously assigned board still has room for them
        if current_board_counts.get(previously_assigned_board, 0) < 200:
            log.info(f"{author} ({author.id}) was already assigned to a board with open slots.")
            return AdventOfCode.leaderboards[previously_assigned_board].join_code

        log.info(
            f"User {author} ({author.id}) previously received the join code for "
            f"board `{previously_assigned_board}`, but that board's now full. "
            "Assigning another board to this user."
        )

    # If we don't have the current board counts cached, let's force fetching a new cache
    if not current_board_counts:
        log.warning("Leaderboard counts were missing from the cache unexpectedly!")
        await fetch_leaderboard(invalidate_cache=True)
        current_board_counts = await _caches.leaderboard_counts.to_dict()

    # Find the board with the current lowest participant count. As we can't
    best_board, _count = min(current_board_counts.items(), key=operator.itemgetter(1))

    if current_board_counts.get(best_board, 0) >= 200:
        log.warning(f"User {author} `{author.id}` requested a join code, but all boards are full!")
        return

    log.info(f"Assigning user {author} ({author.id}) to board `{best_board}`")
    await _caches.assigned_leaderboard.set(author.id, best_board)

    # Return the join code for this board
    return AdventOfCode.leaderboards[best_board].join_code


def is_in_advent() -> bool:
    """
    Check if we're currently on an Advent of Code day, excluding 25 December.

    This helper function is used to check whether or not a feature that prepares
    something for the next Advent of Code challenge should run. As the puzzle
    published on the 25th is the last puzzle, this check excludes that date.
    """
    return arrow.now(EST).day in range(1, 25) and arrow.now(EST).month == 12


def time_left_to_est_midnight() -> tuple[datetime.datetime, datetime.timedelta]:
    """Calculate the amount of time left until midnight EST/UTC-5."""
    # Change all time properties back to 00:00
    todays_midnight = arrow.now(EST).replace(
        microsecond=0,
        second=0,
        minute=0,
        hour=0
    )

    # We want tomorrow so add a day on
    tomorrow = todays_midnight + datetime.timedelta(days=1)

    # Calculate the timedelta between the current time and midnight
    return tomorrow, tomorrow - arrow.now(EST)


async def wait_for_advent_of_code(*, hours_before: int = 1) -> None:
    """
    Wait for the Advent of Code event to start.

    This function returns `hours_before` (default: 1) the Advent of Code
    actually starts. This allows functions to schedule and execute code that
    needs to run before the event starts.

    If the event has already started, this function returns immediately.

    Note: The "next Advent of Code" is determined based on the current value
    of the `AOC_YEAR` environment variable. This allows callers to exit early
    if we're already past the Advent of Code edition the bot is currently
    configured for.
    """
    start = arrow.get(datetime.datetime(AdventOfCode.year, 12, 1), EST)
    target = start - datetime.timedelta(hours=hours_before)
    now = arrow.now(EST)

    # If we've already reached or passed to target, we
    # simply return immediately.
    if now >= target:
        return

    delta = target - now
    await asyncio.sleep(delta.total_seconds())


async def countdown_status(bot: Bot) -> None:
    """
    Add the time until the next challenge is published to the bot's status.

    This function sleeps until 2 hours before the event and exists one hour
    after the last challenge has been published. It will not start up again
    automatically for next year's event, as it will wait for the environment
    variable AOC_YEAR to be updated.

    This ensures that the task will only start sleeping again once the next
    event approaches and we're making preparations for that event.
    """
    log.debug("Initializing status countdown task.")
    # We wait until 2 hours before the event starts. Then we
    # set our first countdown status.
    await wait_for_advent_of_code(hours_before=2)

    # Log that we're going to start with the countdown status.
    log.info("The Advent of Code has started or will start soon, starting countdown status.")

    # Trying to change status too early in the bot's startup sequence will fail
    # the task because the websocket instance has not yet been created. Waiting
    # for this event means that both the websocket instance has been initialized
    # and that the connection to Discord is mature enough to change the presence
    # of the bot.
    await bot.wait_until_guild_available()

    # Calculate when the task needs to stop running. To prevent the task from
    # sleeping for the entire year, it will only wait in the currently
    # configured year. This means that the task will only start hibernating once
    # we start preparing the next event by changing environment variables.
    last_challenge = arrow.get(datetime.datetime(AdventOfCode.year, 12, 25), EST)
    end = last_challenge + datetime.timedelta(hours=1)

    while arrow.now(EST) < end:
        _, time_left = time_left_to_est_midnight()

        aligned_seconds = int(math.ceil(time_left.seconds / COUNTDOWN_STEP)) * COUNTDOWN_STEP
        hours, minutes = aligned_seconds // 3600, aligned_seconds // 60 % 60

        if aligned_seconds == 0:
            playing = "right now!"
        elif aligned_seconds == COUNTDOWN_STEP:
            playing = f"in less than {minutes} minutes"
        elif hours == 0:
            playing = f"in {minutes} minutes"
        elif hours == 23:
            playing = f"since {60 - minutes} minutes ago"
        else:
            playing = f"in {hours} hours and {minutes} minutes"

        log.trace(f"Changing presence to {playing!r}")
        # Status will look like "Playing in 5 hours and 30 minutes"
        await bot.change_presence(activity=discord.Game(playing))

        # Sleep until next aligned time or a full step if already aligned
        delay = time_left.seconds % COUNTDOWN_STEP or COUNTDOWN_STEP
        log.trace(f"The countdown status task will sleep for {delay} seconds.")
        await asyncio.sleep(delay)


async def new_puzzle_notification(bot: Bot) -> None:
    """
    Announce the release of a new Advent of Code puzzle.

    This background task hibernates until just before the Advent of Code starts
    and will then start announcing puzzles as they are published. After the
    event has finished, this task will terminate.
    """
    # We wake up one hour before the event starts to prepare the announcement
    # of the release of the first puzzle.
    await wait_for_advent_of_code(hours_before=1)

    log.info("The Advent of Code has started or will start soon, waking up notification task.")

    # Ensure that the guild cache is loaded so we can get the Advent of Code
    # channel and role.
    await bot.wait_until_guild_available()
    aoc_channel = bot.get_channel(Channels.advent_of_code)
    aoc_role = aoc_channel.guild.get_role(AdventOfCode.role_id)

    if not aoc_channel:
        log.error("Could not find the AoC channel to send notification in")
        return

    if not aoc_role:
        log.error("Could not find the AoC role to announce the daily puzzle")
        return

    # The last event day is 25 December, so we only have to schedule
    # a reminder if the current day is before 25 December.
    end = arrow.get(datetime.datetime(AdventOfCode.year, 12, 25), EST)
    while arrow.now(EST) < end:
        log.trace("Started puzzle notification loop.")
        tomorrow, time_left = time_left_to_est_midnight()

        # Use `total_seconds` to get the time left in fractional seconds This
        # should wake us up very close to the target. As a safe guard, the sleep
        # duration is padded with 0.1 second to make sure we wake up after
        # midnight.
        sleep_seconds = time_left.total_seconds() + 0.1
        log.trace(f"The puzzle notification task will sleep for {sleep_seconds} seconds")
        await asyncio.sleep(sleep_seconds)

        puzzle_url = f"https://adventofcode.com/{AdventOfCode.year}/day/{tomorrow.day}"

        # Check if the puzzle is already available to prevent our members from spamming
        # the puzzle page before it's available by making a small HEAD request.
        for retry in range(1, 5):
            log.debug(f"Checking if the puzzle is already available (attempt {retry}/4)")
            async with bot.http_session.head(puzzle_url, raise_for_status=False) as resp:
                if resp.status == 200:
                    log.debug("Puzzle is available; let's send an announcement message.")
                    break
            log.debug(f"The puzzle is not yet available (status={resp.status})")
            await asyncio.sleep(10)
        else:
            log.error(
                "The puzzle does does not appear to be available "
                "at this time, canceling announcement"
            )
            break

        await aoc_channel.send(
            f"{aoc_role.mention} Good morning! Day {tomorrow.day} is ready to be attempted. "
            f"View it online now at {puzzle_url}. Good luck!",
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                users=False,
                roles=[aoc_role],
            )
        )

        # Ensure that we don't send duplicate announcements by sleeping to well
        # over midnight. This means we're certain to calculate the time to the
        # next midnight at the top of the loop.
        await asyncio.sleep(120)


def background_task_callback(task: asyncio.Task) -> None:
    """Check if the finished background task failed to make sure we log errors."""
    if task.cancelled():
        log.info(f"Background task `{task.get_name()}` was cancelled.")
    elif exception := task.exception():
        log.error(f"Background task `{task.get_name()}` failed:", exc_info=exception)
    else:
        log.info(f"Background task `{task.get_name()}` exited normally.")

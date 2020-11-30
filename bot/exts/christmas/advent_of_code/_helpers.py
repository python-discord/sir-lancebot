import collections
import datetime
import json
import logging
import operator
import typing

import aiohttp
import discord

from bot.constants import AdventOfCode, Colours
from bot.exts.christmas.advent_of_code import _caches

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
    "/branding/master/seasonal/christmas/server_icons/festive_256.gif"
)

# Create namedtuple that combines a participant's name and their completion
# time for a specific star. We're going to use this later to order the results
# for each star to compute the rank score.
_StarResult = collections.namedtuple("StarResult", "name completion_time")


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
    for member in raw_leaderboard_data.values():
        name = member["name"] if member["name"] else f"Anonymous #{member['id']}"
        leaderboard[name] = {"score": 0, "star_1_count": 0, "star_2_count": 0}

        # Iterate over all days for this participant
        for day, stars in member["completion_day_level"].items():
            # Iterate over the complete stars for this day for this participant
            for star, data in stars.items():
                # Record completion of this star for this individual
                leaderboard[name][f"star_{star}_count"] += 1

                # Record completion datetime for this participant for this day/star
                completion_time = datetime.datetime.fromtimestamp(int(data['get_star_ts']))
                star_results[(day, star)].append(
                    _StarResult(name=name, completion_time=completion_time)
                )

    # Now that we have a transposed dataset that holds the completion time of all
    # participants per star, we can compute the rank-based scores each participant
    # should get for that star.
    max_score = len(leaderboard)
    for star in star_results.values():
        for rank, star_result in enumerate(sorted(star, key=operator.itemgetter(1))):
            leaderboard[star_result.name]["score"] += max_score - rank

    # Since dictionaries now retain insertion order, let's use that
    sorted_leaderboard = dict(
        sorted(leaderboard.items(), key=lambda t: t[1]["score"], reverse=True)
    )

    daily_stats = {}
    for day in range(1, 26):
        star_one = len(star_results.get((day, 1), []))
        star_two = len(star_results.get((day, 1), []))
        daily_stats[day] = {"star_one": star_one, "star_two": star_two}

    return {"daily_stats": daily_stats, "leaderboard": sorted_leaderboard}


def _format_leaderboard(leaderboard: typing.Dict[str, int]) -> str:
    """Format the leaderboard using the AOC_TABLE_TEMPLATE."""
    leaderboard_lines = [HEADER]
    for rank, (name, results) in enumerate(leaderboard.items(), start=1):
        leaderboard_lines.append(
            AOC_TABLE_TEMPLATE.format(
                rank=rank,
                name=name,
                score=str(results["score"]),
                stars=f"({results['star_1_count']}, {results['star_2_count']})"
            )
        )

    return "\n".join(leaderboard_lines)


async def _fetch_leaderboard_data() -> typing.Dict[str, typing.Any]:
    """Fetch data for all leaderboards and return a pooled result."""
    year = AdventOfCode.year

    # We'll make our requests one at a time to not flood the AoC website with
    # up to six simultaneous requests. This may take a little longer, but it
    # does avoid putting unnecessary stress on the Advent of Code website.

    # Container to store the raw data of each leaderboard
    participants = {}
    for leaderboard in AdventOfCode.leaderboards.values():
        leaderboard_url = AOC_API_URL.format(year=year, leaderboard_id=leaderboard.id)
        cookies = {"session": leaderboard.session}

        # We don't need to create a session if we're going to throw it away after each request
        async with aiohttp.request(
            "GET", leaderboard_url, headers=AOC_REQUEST_HEADER, cookies=cookies
        ) as resp:
            if resp.status == 200:
                raw_data = await resp.json()

                # Get the participants and store their current count
                board_participants = raw_data["members"]
                await _caches.leaderboard_counts.set(leaderboard.id, len(board_participants))
                participants.update(board_participants)
            else:
                log.warning(f"Fetching data failed for leaderboard `{leaderboard.id}`")
                resp.raise_for_status()

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
async def fetch_leaderboard(invalidate_cache: bool = False) -> dict:
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
        leaderboard_fetched_at = datetime.datetime.utcnow().isoformat()

        cached_leaderboard = {
            "full_leaderboard": formatted_leaderboard,
            "top_leaderboard": _get_top_leaderboard(formatted_leaderboard),
            "full_leaderboard_url": full_leaderboard_url,
            "leaderboard_fetched_at": leaderboard_fetched_at,
            "number_of_participants": number_of_participants,
            "daily_stats": json.dumps(parsed_leaderboard_data["daily_stats"]),
        }

        # Store the new values in Redis
        await _caches.leaderboard_cache.update(cached_leaderboard)

        # Set an expiry on the leaderboard RedisCache
        with await _caches.leaderboard_cache._get_pool_connection() as connection:
            await connection.expire(
                _caches.leaderboard_cache.namespace,
                AdventOfCode.leaderboard_cache_expiry_seconds
            )

    return cached_leaderboard


def get_summary_embed(leaderboard: dict) -> discord.Embed:
    """Get an embed with the current summary stats of the leaderboard."""
    leaderboard_url = leaderboard['full_leaderboard_url']

    aoc_embed = discord.Embed(
        colour=Colours.soft_green,
        timestamp=datetime.datetime.fromisoformat(leaderboard["leaderboard_fetched_at"]),
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
    aoc_embed.set_footer(text="Last Updated")
    aoc_embed.set_thumbnail(url=AOC_EMBED_THUMBNAIL)

    return aoc_embed


async def get_public_join_code(author: discord.Member) -> typing.Optional[str]:
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

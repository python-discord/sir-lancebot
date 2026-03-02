from __future__ import annotations

from typing import TYPE_CHECKING

from async_rediscache import RedisCache
from pydis_core.utils.logging import get_logger

from bot.utils.quote import seconds_until_midnight_utc

if TYPE_CHECKING:
    from bot.bot import Bot

log = get_logger(__name__)

# Maximum points a user can earn per game per day.
DAILY_POINT_CAP = 100

# Prefix for daily cap keys stored directly in Redis (not via RedisCache).
_DAILY_KEY_PREFIX = "leaderboard:daily"


def _daily_key(user_id: int, game_name: str) -> str:
    """Build a namespaced Redis key for daily point tracking."""
    return f"{_DAILY_KEY_PREFIX}:{user_id}:{game_name}"


async def _get_points_cache() -> RedisCache:
    """Get the persistent points cache from the Leaderboard cog."""
    from bot.exts.fun.leaderboard import Leaderboard
    return Leaderboard.points_cache


async def add_points(bot: Bot, user_id: int, points: int, game_name: str) -> tuple[int, int]:
    """
    Add points to a user's global leaderboard score.

    Points are clamped by the daily cap per game ("DAILY_POINT_CAP").
    Daily entries expire automatically at UTC midnight via Redis TTL.

    Returns a tuple of (new_total_score, points_actually_earned).
    Returns (0, 0) if the cog is not loaded.
    """
    if points <= 0:
        total = await get_user_points(bot, user_id)
        return (total, 0)

    if bot.get_cog("Leaderboard") is None:
        return (0, 0)

    redis = bot.redis_session.client
    daily_key = _daily_key(user_id, game_name)

    # enforce daily cap
    earned_today = await redis.get(daily_key)
    earned_today = int(earned_today) if earned_today else 0

    remaining = DAILY_POINT_CAP - earned_today
    if remaining <= 0:
        log.trace(f"User {user_id} hit daily cap for {game_name}, skipping.")
        total = await get_user_points(bot, user_id)
        return (total, 0)

    # clamp to remaining daily allowance
    points_earned = min(points, remaining)

    ttl = seconds_until_midnight_utc()
    await redis.set(daily_key, earned_today + points_earned, ex=ttl)

    # update persistent global total
    points_cache = await _get_points_cache()
    if await points_cache.contains(user_id):
        await points_cache.increment(user_id, points_earned)
    else:
        await points_cache.set(user_id, points_earned)

    new_total = int(await points_cache.get(user_id))
    return (new_total, points_earned)


async def remove_points(bot: Bot, user_id: int, points: int) -> int:
    """
    Remove points from a user's global leaderboard score.

    Score will not go below 0. Returns the user's new total score,
    or 0 if the cog is not loaded.
    """
    if points <= 0 or bot.get_cog("Leaderboard") is None:
        return await get_user_points(bot, user_id)

    points_cache = await _get_points_cache()

    current = await points_cache.get(user_id)
    if not current:
        return 0

    current = int(current)
    to_remove = min(points, current)
    await points_cache.decrement(user_id, to_remove)

    return current - to_remove


async def get_leaderboard(bot: Bot) -> list[tuple[int, int]]:
    """
    Get all players from the global leaderboard.

    Returns a list of (user_id, score) tuples sorted by score descending.
    """
    if bot.get_cog("Leaderboard") is None:
        return []

    points_cache = await _get_points_cache()
    records = await points_cache.items()

    return sorted(
        ((int(user_id), int(score)) for user_id, score in records if int(score) > 0),
        key=operator.itemgetter(1),
        reverse=True,
    )


async def get_daily_leaderboard(bot: Bot) -> list[tuple[int, int]]:
    """
    Get today's leaderboard by scanning daily Redis TTL keys.

    Returns a list of (user_id, total_daily_score) tuples sorted descending.
    """
    if bot.get_cog("Leaderboard") is None:
        return []

    redis = bot.redis_session.client
    today_scores: dict[int, int] = {}

    async for key in redis.scan_iter(match=f"{_DAILY_KEY_PREFIX}:*"):
        parts = key.split(":")
        if len(parts) != 4:
            continue
        user_id = int(parts[2])
        points = int(await redis.get(key) or 0)
        today_scores[user_id] = today_scores.get(user_id, 0) + points

    return sorted(
        ((uid, score) for uid, score in today_scores.items() if score > 0),
        key=lambda x: x[1],
        reverse=True,
    )


async def get_user_rank(
    bot: Bot,
    user_id: int,
    leaderboard: list[tuple[int, int]] | None = None,
) -> int | None:
    """
    Get a user's rank on the global leaderboard, or None if unranked.

    Users with the same score share a rank.
    """
    if leaderboard is None:
        leaderboard = await get_leaderboard(bot)

    prev_score = None
    rank = 0

    for position, (uid, score) in enumerate(leaderboard, start=1):
        if score != prev_score:
            rank = position
            prev_score = score

        if uid == user_id:
            return rank

    return None


async def get_user_points(bot: Bot, user_id: int) -> int:
    """Get a specific user's total points."""
    if bot.get_cog("Leaderboard") is None:
        return 0

    points_cache = await _get_points_cache()
    score = await points_cache.get(user_id)
    return int(score) if score else 0

from os import environ

class Colours:
    soft_red = 0xcd6d6d
    soft_green = 0x68c290

class Emojis:
    star = "\u2B50"
    christmas_tree = u"\U0001F384"

class AdventOfCode:
    leaderboard_cache_age_threshold_seconds = 3600
    leaderboard_id = 363275
    leaderboard_join_code = "363275-442b6939"
    leaderboard_max_displayed_members = 10
    session_cookie = environ.get("AOC_SESSION_COOKIE")
    year = 2018
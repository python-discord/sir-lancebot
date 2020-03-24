import enum
import logging
from datetime import datetime
from os import environ
from typing import NamedTuple

__all__ = (
    "AdventOfCode", "Branding", "Channels", "Client", "Colours", "Emojis", "Hacktoberfest", "Month", "Roles", "Tokens",
    "WHITELISTED_CHANNELS", "STAFF_ROLES", "MODERATION_ROLES",
    "POSITIVE_REPLIES", "NEGATIVE_REPLIES", "ERROR_REPLIES",
)

log = logging.getLogger(__name__)


class AdventOfCode:
    leaderboard_cache_age_threshold_seconds = 3600
    leaderboard_id = 631135
    leaderboard_join_code = str(environ.get("AOC_JOIN_CODE", None))
    leaderboard_max_displayed_members = 10
    year = int(environ.get("AOC_YEAR", datetime.utcnow().year))
    role_id = int(environ.get("AOC_ROLE_ID", 518565788744024082))


class Channels(NamedTuple):
    admins = 365960823622991872
    advent_of_code = int(environ.get("AOC_CHANNEL_ID", 517745814039166986))
    announcements = int(environ.get("CHANNEL_ANNOUNCEMENTS", 354619224620138496))
    big_brother_logs = 468507907357409333
    bot = 267659945086812160
    checkpoint_test = 422077681434099723
    devalerts = 460181980097675264
    devlog = int(environ.get("CHANNEL_DEVLOG", 622895325144940554))
    devtest = 414574275865870337
    help_0 = 303906576991780866
    help_1 = 303906556754395136
    help_2 = 303906514266226689
    help_3 = 439702951246692352
    help_4 = 451312046647148554
    help_5 = 454941769734422538
    helpers = 385474242440986624
    message_log = 467752170159079424
    mod_alerts = 473092532147060736
    modlog = 282638479504965634
    off_topic_0 = 291284109232308226
    off_topic_1 = 463035241142026251
    off_topic_2 = 463035268514185226
    python = 267624335836053506
    reddit = 458224812528238616
    seasonalbot_commands = int(environ.get("CHANNEL_SEASONALBOT_COMMANDS", 607247579608121354))
    seasonalbot_voice = int(environ.get("CHANNEL_SEASONALBOT_VOICE", 606259004230074378))
    staff_lounge = 464905259261755392
    verification = 352442727016693763
    python_discussion = 267624335836053506
    show_your_projects = int(environ.get("CHANNEL_SHOW_YOUR_PROJECTS", 303934982764625920))
    show_your_projects_discussion = 360148304664723466
    hacktoberfest_2019 = 628184417646411776


class Branding:
    cycle_frequency = int(environ.get("CYCLE_FREQUENCY", 3))  # 0: never, 1: every day, 2: every other day, ...
    autostart = environ.get("BRANDING_AUTOSTART", "").lower() == "true"  # Launch the branding daemon on start-up


class Client(NamedTuple):
    guild = int(environ.get("SEASONALBOT_GUILD", 267624335836053506))
    prefix = environ.get("PREFIX", ".")
    token = environ.get("SEASONALBOT_TOKEN")
    debug = environ.get("SEASONALBOT_DEBUG", "").lower() == "true"


class Colours:
    blue = 0x0279fd
    bright_green = 0x01d277
    dark_green = 0x1f8b4c
    orange = 0xe67e22
    pink = 0xcf84e0
    soft_green = 0x68c290
    soft_red = 0xcd6d6d
    yellow = 0xf9f586
    purple = 0xb734eb


class Emojis:
    star = "\u2B50"
    christmas_tree = "\U0001F384"
    check = "\u2611"
    envelope = "\U0001F4E8"
    trashcan = "<:trashcan:637136429717389331>"
    ok_hand = ":ok_hand:"

    terning1 = "<:terning1:431249668983488527>"
    terning2 = "<:terning2:462339216987127808>"
    terning3 = "<:terning3:431249694467948544>"
    terning4 = "<:terning4:579980271475228682>"
    terning5 = "<:terning5:431249716328792064>"
    terning6 = "<:terning6:431249726705369098>"

    issue = "<:IssueOpen:629695470327037963>"
    issue_closed = "<:IssueClosed:629695470570307614>"
    pull_request = "<:PROpen:629695470175780875>"
    pull_request_closed = "<:PRClosed:629695470519713818>"
    merge = "<:PRMerged:629695470570176522>"


class Icons:
    questionmark = "https://cdn.discordapp.com/emojis/512367613339369475.png"
    bookmark = (
        "https://images-ext-2.discordapp.net/external/zl4oDwcmxUILY7sD9ZWE2fU5R7n6QcxEmPYSE5eddbg/"
        "%3Fv%3D1/https/cdn.discordapp.com/emojis/654080405988966419.png?width=20&height=20"
    )


class Lovefest:
    role_id = int(environ.get("LOVEFEST_ROLE_ID", 542431903886606399))


class Hacktoberfest(NamedTuple):
    voice_id = 514420006474219521


class Month(enum.IntEnum):
    january = 1
    february = 2
    march = 3
    april = 4
    may = 5
    june = 6
    july = 7
    august = 8
    september = 9
    october = 10
    november = 11
    december = 12


class Roles(NamedTuple):
    admin = int(environ.get("SEASONALBOT_ADMIN_ROLE_ID", 267628507062992896))
    announcements = 463658397560995840
    champion = 430492892331769857
    contributor = 295488872404484098
    developer = 352427296948486144
    devops = 409416496733880320
    jammer = 423054537079783434
    moderator = 267629731250176001
    muted = 277914926603829249
    owner = 267627879762755584
    verified = 352427296948486144
    helpers = 267630620367257601
    rockstars = 458226413825294336


class Tokens(NamedTuple):
    giphy = environ.get("GIPHY_TOKEN")
    aoc_session_cookie = environ.get("AOC_SESSION_COOKIE")
    omdb = environ.get("OMDB_API_KEY")
    youtube = environ.get("YOUTUBE_API_KEY")
    tmdb = environ.get("TMDB_API_KEY")
    igdb = environ.get("IGDB_API_KEY")
    github = environ.get("GITHUB_TOKEN")


# Default role combinations
MODERATION_ROLES = Roles.moderator, Roles.admin, Roles.owner
STAFF_ROLES = Roles.helpers, Roles.moderator, Roles.admin, Roles.owner

# Whitelisted channels
WHITELISTED_CHANNELS = (
    Channels.bot, Channels.seasonalbot_commands,
    Channels.off_topic_0, Channels.off_topic_1, Channels.off_topic_2,
    Channels.devtest,
)

# Bot replies
NEGATIVE_REPLIES = [
    "Noooooo!!",
    "Nope.",
    "I'm sorry Dave, I'm afraid I can't do that.",
    "I don't think so.",
    "Not gonna happen.",
    "Out of the question.",
    "Huh? No.",
    "Nah.",
    "Naw.",
    "Not likely.",
    "No way, José.",
    "Not in a million years.",
    "Fat chance.",
    "Certainly not.",
    "NEGATORY.",
    "Nuh-uh.",
    "Not in my house!",
]

POSITIVE_REPLIES = [
    "Yep.",
    "Absolutely!",
    "Can do!",
    "Affirmative!",
    "Yeah okay.",
    "Sure.",
    "Sure thing!",
    "You're the boss!",
    "Okay.",
    "No problem.",
    "I got you.",
    "Alright.",
    "You got it!",
    "ROGER THAT",
    "Of course!",
    "Aye aye, cap'n!",
    "I'll allow it.",
]

ERROR_REPLIES = [
    "Please don't do that.",
    "You have to stop.",
    "Do you mind?",
    "In the future, don't do that.",
    "That was a mistake.",
    "You blew it.",
    "You're bad at computers.",
    "Are you trying to kill me?",
    "Noooooo!!",
    "I can't believe you've done this",
]

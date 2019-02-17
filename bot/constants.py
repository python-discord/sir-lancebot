import logging
from os import environ
from typing import NamedTuple

from bot.bot import SeasonalBot

__all__ = (
    "AdventOfCode", "Channels", "Client", "Colours", "Emojis", "Hacktoberfest", "Roles",
    "Tokens", "bot"
)

log = logging.getLogger(__name__)


class AdventOfCode:
    leaderboard_cache_age_threshold_seconds = 3600
    leaderboard_id = 363275
    leaderboard_join_code = "363275-442b6939"
    leaderboard_max_displayed_members = 10
    year = 2018
    channel_id = int(environ.get("AOC_CHANNEL_ID", 517745814039166986))
    role_id = int(environ.get("AOC_ROLE_ID", 518565788744024082))


class Channels(NamedTuple):
    admins = 365960823622991872
    announcements = int(environ.get('CHANNEL_ANNOUNCEMENTS', 354619224620138496))
    big_brother_logs = 468507907357409333
    bot = 267659945086812160
    checkpoint_test = 422077681434099723
    devalerts = 460181980097675264
    devlog = int(environ.get('CHANNEL_DEVLOG', 409308876241108992))
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
    staff_lounge = 464905259261755392
    verification = 352442727016693763


class Client(NamedTuple):
    guild = int(environ.get('SEASONALBOT_GUILD', 267624335836053506))
    prefix = "."
    token = environ.get('SEASONALBOT_TOKEN')
    debug = environ.get('SEASONALBOT_DEBUG', '').lower() == 'true'
    season_override = environ.get('SEASON_OVERRIDE')


class Colours:
    soft_red = 0xcd6d6d
    soft_green = 0x68c290
    bright_green = 0x01d277
    dark_green = 0x1f8b4c
    orange = 0xe67e22
    pink = 0xcf84e0


class Emojis:
    star = "\u2B50"
    christmas_tree = "\U0001F384"
    check = "\u2611"


class Lovefest:
    # channel_id = int(environ.get("LOVEFEST_CHANNEL_ID", 542272993192050698))
    channel_id = int(environ.get("LOVEFEST_CHANNEL_ID", 426566445124812815))
    # role_id = int(environ.get("LOVEFEST_ROLE_ID", 542431903886606399))
    role_id = int(environ.get("LOVEFEST_ROLE_ID", 507601744411230208))


class Hacktoberfest(NamedTuple):
    channel_id = 498804484324196362
    voice_id = 514420006474219521


class Roles(NamedTuple):
    admin = int(environ.get('SEASONALBOT_ADMIN_ROLE_ID', 267628507062992896))
    announcements = 463658397560995840
    champion = 430492892331769857
    contributor = 295488872404484098
    developer = 352427296948486144
    devops = 409416496733880320
    jammer = 423054537079783434
    # moderator = 267629731250176001
    moderator = 507601744411230208  # for my local server, never add this file
    muted = 277914926603829249
    owner = 267627879762755584
    verified = 352427296948486144
    helpers = 267630620367257601
    rockstars = 458226413825294336


class Tokens(NamedTuple):
    giphy = environ.get("GIPHY_TOKEN")
    aoc_session_cookie = environ.get("AOC_SESSION_COOKIE")


bot = SeasonalBot(command_prefix=Client.prefix)

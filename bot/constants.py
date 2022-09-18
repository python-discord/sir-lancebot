import dataclasses
import enum
import logging
from datetime import datetime
from os import environ
from typing import NamedTuple

__all__ = (
    "AdventOfCode",
    "Branding",
    "Cats",
    "Channels",
    "Categories",
    "Client",
    "Logging",
    "Colours",
    "Emojis",
    "Icons",
    "Lovefest",
    "Month",
    "Roles",
    "Tokens",
    "Wolfram",
    "Reddit",
    "RedisConfig",
    "RedirectOutput",
    "PYTHON_PREFIX",
    "MODERATION_ROLES",
    "STAFF_ROLES",
    "WHITELISTED_CHANNELS",
    "ERROR_REPLIES",
    "NEGATIVE_REPLIES",
    "POSITIVE_REPLIES",
)

log = logging.getLogger(__name__)


PYTHON_PREFIX = "!"


@dataclasses.dataclass
class AdventOfCodeLeaderboard:
    id: str
    _session: str
    join_code: str

    # If we notice that the session for this board expired, we set
    # this attribute to `True`. We will emit a Sentry error so we
    # can handle it, but, in the meantime, we'll try using the
    # fallback session to make sure the commands still work.
    use_fallback_session: bool = False

    @property
    def session(self) -> str:
        """Return either the actual `session` cookie or the fallback cookie."""
        if self.use_fallback_session:
            log.trace(f"Returning fallback cookie for board `{self.id}`.")
            return AdventOfCode.fallback_session

        return self._session


def _parse_aoc_leaderboard_env() -> dict[str, AdventOfCodeLeaderboard]:
    """
    Parse the environment variable containing leaderboard information.

    A leaderboard should be specified in the format `id,session,join_code`,
    without the backticks. If more than one leaderboard needs to be added to
    the constant, separate the individual leaderboards with `::`.

    Example ENV: `id1,session1,join_code1::id2,session2,join_code2`
    """
    raw_leaderboards = environ.get("AOC_LEADERBOARDS", "")
    if not raw_leaderboards:
        return {}

    leaderboards = {}
    for leaderboard in raw_leaderboards.split("::"):
        leaderboard_id, session, join_code = leaderboard.split(",")
        leaderboards[leaderboard_id] = AdventOfCodeLeaderboard(leaderboard_id, session, join_code)

    return leaderboards


class AdventOfCode:
    # Information for the several leaderboards we have
    leaderboards = _parse_aoc_leaderboard_env()
    staff_leaderboard_id = environ.get("AOC_STAFF_LEADERBOARD_ID", "")
    fallback_session = environ.get("AOC_FALLBACK_SESSION", "")

    # Other Advent of Code constants
    ignored_days = environ.get("AOC_IGNORED_DAYS", "").split(",")
    leaderboard_displayed_members = 10
    leaderboard_cache_expiry_seconds = 1800
    max_day_and_star_results = 15
    year = int(environ.get("AOC_YEAR", datetime.utcnow().year))
    role_id = int(environ.get("AOC_ROLE_ID", 518565788744024082))


class Branding:
    cycle_frequency = int(environ.get("CYCLE_FREQUENCY", 3))  # 0: never, 1: every day, 2: every other day, ...


class Cats:
    cats = ["ᓚᘏᗢ", "ᘡᘏᗢ", "🐈", "ᓕᘏᗢ", "ᓇᘏᗢ", "ᓂᘏᗢ", "ᘣᘏᗢ", "ᕦᘏᗢ", "ᕂᘏᗢ"]


class Channels(NamedTuple):
    advent_of_code = int(environ.get("AOC_CHANNEL_ID", 897932085766004786))
    advent_of_code_commands = int(environ.get("AOC_COMMANDS_CHANNEL_ID", 897932607545823342))
    algos_and_data_structs = 650401909852864553
    bot_commands = 267659945086812160
    community_meta = 267659945086812160
    organisation = 551789653284356126
    data_science_and_ai = 366673247892275221
    devlog = int(environ.get("CHANNEL_DEVLOG", 622895325144940554))
    dev_contrib = 635950537262759947
    mod_meta = 775412552795947058
    mod_tools = 775413915391098921
    off_topic_0 = 291284109232308226
    off_topic_1 = 463035241142026251
    off_topic_2 = 463035268514185226
    sir_lancebot_playground = int(environ.get("CHANNEL_COMMUNITY_BOT_COMMANDS", 607247579608121354))
    voice_chat_0 = 412357430186344448
    voice_chat_1 = 799647045886541885
    staff_voice = 541638762007101470
    reddit = int(environ.get("CHANNEL_REDDIT", 458224812528238616))


class Categories(NamedTuple):
    help_in_use = 696958401460043776
    development = 411199786025484308
    devprojects = 787641585624940544
    media = 799054581991997460
    staff = 364918151625965579


codejam_categories_name = "Code Jam"  # Name of the codejam team categories


class Client(NamedTuple):
    name = "Sir Lancebot"
    guild = int(environ.get("BOT_GUILD", 267624335836053506))
    prefix = environ.get("PREFIX", ".")
    token = environ.get("BOT_TOKEN")
    debug = environ.get("BOT_DEBUG", "true").lower() == "true"
    in_ci = environ.get("IN_CI", "false").lower() == "true"
    github_bot_repo = "https://github.com/python-discord/sir-lancebot"
    # Override seasonal locks: 1 (January) to 12 (December)
    month_override = int(environ["MONTH_OVERRIDE"]) if "MONTH_OVERRIDE" in environ else None


class Logging(NamedTuple):
    debug = Client.debug
    file_logs = environ.get("FILE_LOGS", "false").lower() == "true"
    trace_loggers = environ.get("BOT_TRACE_LOGGERS")


class Colours:
    blue = 0x0279FD
    twitter_blue = 0x1DA1F2
    bright_green = 0x01D277
    dark_green = 0x1F8B4C
    orange = 0xE67E22
    pink = 0xCF84E0
    purple = 0xB734EB
    soft_green = 0x68C290
    soft_orange = 0xF9CB54
    soft_red = 0xCD6D6D
    yellow = 0xF9F586
    python_blue = 0x4B8BBE
    python_yellow = 0xFFD43B
    grass_green = 0x66FF00
    gold = 0xE6C200

    easter_like_colours = [
        (255, 247, 0),
        (255, 255, 224),
        (0, 255, 127),
        (189, 252, 201),
        (255, 192, 203),
        (255, 160, 122),
        (181, 115, 220),
        (221, 160, 221),
        (200, 162, 200),
        (238, 130, 238),
        (135, 206, 235),
        (0, 204, 204),
        (64, 224, 208),
    ]


class Emojis:
    cross_mark = "\u274C"
    star = "\u2B50"
    christmas_tree = "\U0001F384"
    check = "\u2611"
    envelope = "\U0001F4E8"
    trashcan = environ.get("TRASHCAN_EMOJI", "<:trashcan:637136429717389331>")
    ok_hand = ":ok_hand:"
    hand_raised = "\U0001F64B"

    dice_1 = "<:dice_1:755891608859443290>"
    dice_2 = "<:dice_2:755891608741740635>"
    dice_3 = "<:dice_3:755891608251138158>"
    dice_4 = "<:dice_4:755891607882039327>"
    dice_5 = "<:dice_5:755891608091885627>"
    dice_6 = "<:dice_6:755891607680843838>"

    # These icons are from Github's repo https://github.com/primer/octicons/
    issue_open = "<:IssueOpen:852596024777506817>"
    issue_closed = "<:IssueClosed:927326162861039626>"
    issue_draft = "<:IssueDraft:852596025147523102>"  # Not currently used by Github, but here for future.
    pull_request_open = "<:PROpen:852596471505223781>"
    pull_request_closed = "<:PRClosed:852596024732286976>"
    pull_request_draft = "<:PRDraft:852596025045680218>"
    pull_request_merged = "<:PRMerged:852596100301193227>"

    number_emojis = {
        1: "\u0031\ufe0f\u20e3",
        2: "\u0032\ufe0f\u20e3",
        3: "\u0033\ufe0f\u20e3",
        4: "\u0034\ufe0f\u20e3",
        5: "\u0035\ufe0f\u20e3",
        6: "\u0036\ufe0f\u20e3",
        7: "\u0037\ufe0f\u20e3",
        8: "\u0038\ufe0f\u20e3",
        9: "\u0039\ufe0f\u20e3"
    }

    confirmation = "\u2705"
    decline = "\u274c"
    incident_unactioned = "<:incident_unactioned:719645583245180960>"

    x = "\U0001f1fd"
    o = "\U0001f1f4"

    x_square = "<:x_square:632278427260682281>"
    o_square = "<:o_square:632278452413661214>"

    status_online = "<:status_online:470326272351010816>"
    status_idle = "<:status_idle:470326266625785866>"
    status_dnd = "<:status_dnd:470326272082313216>"
    status_offline = "<:status_offline:470326266537705472>"

    stackoverflow_tag = "<:stack_tag:870926975307501570>"
    stackoverflow_views = "<:stack_eye:870926992692879371>"

    # Reddit emojis
    reddit = "<:reddit:676030265734332427>"
    reddit_post_text = "<:reddit_post_text:676030265910493204>"
    reddit_post_video = "<:reddit_post_video:676030265839190047>"
    reddit_post_photo = "<:reddit_post_photo:676030265734201344>"
    reddit_upvote = "<:reddit_upvote:755845219890757644>"
    reddit_comments = "<:reddit_comments:755845255001014384>"
    reddit_users = "<:reddit_users:755845303822974997>"

    lemon_hyperpleased = "<:lemon_hyperpleased:754441879822663811>"
    lemon_pensive = "<:lemon_pensive:754441880246419486>"


class Icons:
    questionmark = "https://cdn.discordapp.com/emojis/512367613339369475.png"
    bookmark = (
        "https://images-ext-2.discordapp.net/external/zl4oDwcmxUILY7sD9ZWE2fU5R7n6QcxEmPYSE5eddbg/"
        "%3Fv%3D1/https/cdn.discordapp.com/emojis/654080405988966419.png?width=20&height=20"
    )


class Lovefest:
    role_id = int(environ.get("LOVEFEST_ROLE_ID", 542431903886606399))


class Month(enum.IntEnum):
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12

    def __str__(self) -> str:
        return self.name.title()


# If a month override was configured, check that it's a valid Month
# Prevents delaying an exception after the bot starts
if Client.month_override is not None:
    Month(Client.month_override)


class Roles(NamedTuple):
    owners = 267627879762755584
    admins = int(environ.get("BOT_ADMIN_ROLE_ID", 267628507062992896))
    moderation_team = 267629731250176001
    helpers = int(environ.get("ROLE_HELPERS", 267630620367257601))
    core_developers = 587606783669829632
    everyone = int(environ.get("BOT_GUILD", 267624335836053506))
    aoc_completionist = int(environ.get("AOC_COMPLETIONIST_ROLE_ID", 916691790181056532))


class Tokens(NamedTuple):
    giphy = environ.get("GIPHY_TOKEN")
    aoc_session_cookie = environ.get("AOC_SESSION_COOKIE")
    omdb = environ.get("OMDB_API_KEY")
    youtube = environ.get("YOUTUBE_API_KEY")
    tmdb = environ.get("TMDB_API_KEY")
    nasa = environ.get("NASA_API_KEY")
    igdb_client_id = environ.get("IGDB_CLIENT_ID")
    igdb_client_secret = environ.get("IGDB_CLIENT_SECRET")
    github = environ.get("GITHUB_TOKEN")
    unsplash_access_key = environ.get("UNSPLASH_KEY")


class Wolfram(NamedTuple):
    user_limit_day = int(environ.get("WOLFRAM_USER_LIMIT_DAY", 10))
    guild_limit_day = int(environ.get("WOLFRAM_GUILD_LIMIT_DAY", 67))
    key = environ.get("WOLFRAM_API_KEY")


class RedisConfig(NamedTuple):
    host = environ.get("REDIS_HOST", "redis.default.svc.cluster.local")
    port = environ.get("REDIS_PORT", 6379)
    password = environ.get("REDIS_PASSWORD")
    use_fakeredis = environ.get("USE_FAKEREDIS", "false").lower() == "true"


class Source:
    github = "https://github.com/python-discord/sir-lancebot"
    github_avatar_url = "https://avatars1.githubusercontent.com/u/9919"


class RedirectOutput:
    delete_delay: int = 10


class Reddit:
    subreddits = ["r/Python"]

    client_id = environ.get("REDDIT_CLIENT_ID")
    secret = environ.get("REDDIT_SECRET")
    webhook = int(environ.get("REDDIT_WEBHOOK", 635408384794951680))


# Default role combinations
MODERATION_ROLES = {Roles.moderation_team, Roles.admins, Roles.owners}
STAFF_ROLES = {Roles.helpers, Roles.moderation_team, Roles.admins, Roles.owners}

# Whitelisted channels
WHITELISTED_CHANNELS = (
    Channels.bot_commands,
    Channels.sir_lancebot_playground,
    Channels.off_topic_0,
    Channels.off_topic_1,
    Channels.off_topic_2,
    Channels.voice_chat_0,
    Channels.voice_chat_1,
)

# Bot replies
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

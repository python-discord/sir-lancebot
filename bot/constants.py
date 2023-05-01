import enum
import logging
from os import environ

from pydantic import BaseSettings


__all__ = (
    "Branding",
    "Cats",
    "Channels",
    "Categories",
    "Bot",
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
    "Redis",
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


class EnvConfig(BaseSettings):
    """Our default configuration for models that should load from .env files."""

    class Config:
        """Specify what .env files to load, and how to load them."""

        env_file = ".env.server", ".env",
        env_file_encoding = "utf-8"


class _Branding(EnvConfig):
    EnvConfig.Config.env_prefix = "branding_"

    cycle_frequency = 3  # 0: never, 1: every day, 2: every other day, ...


Branding = _Branding()


class Cats:
    cats = ["ᓚᘏᗢ", "ᘡᘏᗢ", "🐈", "ᓕᘏᗢ", "ᓇᘏᗢ", "ᓂᘏᗢ", "ᘣᘏᗢ", "ᕦᘏᗢ", "ᕂᘏᗢ"]


class _Channels(EnvConfig):
    EnvConfig.Config.env_prefix = "channels_"

    algos_and_data_structs = 650401909852864553
    bot_commands = 267659945086812160
    community_meta = 267659945086812160
    organisation = 551789653284356126
    data_science_and_ai = 366673247892275221
    devlog = 622895325144940554
    dev_contrib = 635950537262759947
    mod_meta = 775412552795947058
    mod_tools = 775413915391098921
    off_topic_0 = 291284109232308226
    off_topic_1 = 463035241142026251
    off_topic_2 = 463035268514185226
    python_help = 1035199133436354600
    sir_lancebot_playground = 607247579608121354
    voice_chat_0 = 412357430186344448
    voice_chat_1 = 799647045886541885
    staff_voice = 541638762007101470
    reddit = 458224812528238616


Channels = _Channels()


class _Categories(EnvConfig):
    EnvConfig.Config.env_prefix = "categories_"

    python_help_system = 691405807388196926
    development = 411199786025484308
    devprojects = 787641585624940544
    media = 799054581991997460
    staff = 364918151625965579


Categories = _Categories()

CODEJAM_CATEGORY_NAME = "Code Jam"  # Name of the codejam team categories


class _Bot(EnvConfig):
    EnvConfig.Config.env_prefix = "bot_"

    name = "Sir Lancebot"
    guild = 267624335836053506
    prefix = "."
    token = ""
    debug = True
    in_ci = False
    github_repo = "https://github.com/python-discord/sir-lancebot"
    # Override seasonal locks: 1 (January) to 12 (December)
    month_override: int | None = None


Bot = _Bot()


class _Logging(EnvConfig):
    EnvConfig.Config.env_prefix = "logging_"

    debug = Bot.debug
    file_logs = False
    trace_loggers = ""


Logging = _Logging()


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
    check = "\u2611"
    envelope = "\U0001F4E8"

    trashcan = environ.get(
        "TRASHCAN_EMOJI",
        "\N{WASTEBASKET}" if Bot.debug else "<:trashcan:637136429717389331>",
    )

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


class _Lovefest(EnvConfig):

    EnvConfig.Config.env_prefix = "lovefest_"

    role_id = 542431903886606399


Lovefest = _Lovefest()


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
if Bot.month_override is not None:
    Month(Bot.month_override)


class _Roles(EnvConfig):

    EnvConfig.Config.env_prefix = "roles_"

    owners = 267627879762755584
    admins = 267628507062992896
    moderation_team = 267629731250176001
    helpers = 267630620367257601
    core_developers = 587606783669829632
    everyone = Bot.guild


Roles = _Roles()


class _Tokens(EnvConfig):
    EnvConfig.Config.env_prefix = "tokens_"

    giphy = ""
    aoc_session_cookie = ""
    omdb = ""
    youtube = ""
    tmdb = ""
    nasa = ""
    igdb_client_id = ""
    igdb_client_secret = ""
    github = ""
    unsplash = ""
    wolfram = ""


Tokens = _Tokens()


class _Wolfram(EnvConfig):
    EnvConfig.Config.env_prefix = "wolfram_"
    user_limit_day = 10
    guild_limit_day = 67


Wolfram = _Wolfram()


class _Redis(EnvConfig):
    EnvConfig.Config.env_prefix = "redis_"

    host = "redis.default.svc.cluster.local"
    port = 6379
    password = ""
    use_fakeredis = False


Redis = _Redis()


class Source:
    github = "https://github.com/python-discord/sir-lancebot"
    github_avatar_url = "https://avatars1.githubusercontent.com/u/9919"


class RedirectOutput:
    delete_delay: int = 10


class _Reddit(EnvConfig):
    EnvConfig.Config.env_prefix = "reddit_"

    subreddits = ["r/Python"]

    client_id = ""
    secret = ""
    webhook = 635408384794951680


Reddit = _Reddit()

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

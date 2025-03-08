import enum
from os import environ
from types import MappingProxyType

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from pydis_core.utils.logging import get_logger

__all__ = (
    "ERROR_REPLIES",
    "MODERATION_ROLES",
    "NEGATIVE_REPLIES",
    "POSITIVE_REPLIES",
    "PYTHON_PREFIX",
    "STAFF_ROLES",
    "WHITELISTED_CHANNELS",
    "Categories",
    "Channels",
    "Client",
    "Colours",
    "Emojis",
    "Icons",
    "Logging",
    "Month",
    "Reddit",
    "Redis",
    "Roles",
    "Tokens",
    "Wolfram",
)

log = get_logger(__name__)


PYTHON_PREFIX = "!"
GIT_SHA = environ.get("GIT_SHA", "development")


class EnvConfig(
    BaseSettings,
    env_file=(".env.server", ".env"),
    env_file_encoding="utf-8",
    env_nested_delimiter="__",
    extra="ignore",
):
    """Our default configuration for models that should load from .env files."""


class _Channels(EnvConfig, env_prefix="channels_"):
    general: int = 123123123123
    algos_and_data_structs: int = 650401909852864553
    bot_commands: int = 267659945086812160
    community_meta: int = 267659945086812160
    data_science_and_ai: int = 366673247892275221
    devlog: int = 622895325144940554
    dev_contrib: int = 635950537262759947
    off_topic_0: int = 291284109232308226
    off_topic_1: int = 463035241142026251
    off_topic_2: int = 463035268514185226
    python_help: int = 1035199133436354600
    sir_lancebot_playground: int = 607247579608121354
    voice_chat_0: int = 412357430186344448
    voice_chat_1: int = 799647045886541885
    reddit: int = 458224812528238616


Channels = _Channels()


class _Categories(EnvConfig, env_prefix="categories_"):
    python_help_system: int = 691405807388196926
    development: int = 411199786025484308
    media: int = 799054581991997460


Categories = _Categories()


class _Client(EnvConfig, env_prefix="client_"):
    name: str = "Sir Lancebot"
    guild: int = 267624335836053506
    prefix: str = "."
    token: SecretStr
    debug: bool = True
    in_ci: bool = False
    github_repo: str = "https://github.com/python-discord/sir-lancebot"
    # Override seasonal locks: 1 (January) to 12 (December)
    month_override: int | None = None
    sentry_dsn: str = ""


Client = _Client()


class _Logging(EnvConfig, env_prefix="logging_"):
    debug: bool = Client.debug
    file_logs: bool = False
    trace_loggers: str = ""


Logging = _Logging()


class Colours:
    """Lookups for commonly used colours."""

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

    easter_like_colours = (
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
    )


class Emojis:
    """Commonly used emojis."""

    cross_mark = "\u274C"
    check = "\u2611"

    trashcan = environ.get(
        "TRASHCAN_EMOJI",
        "\N{WASTEBASKET}" if Client.debug else "<:trashcan:637136429717389331>",
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
    issue_completed = "<:IssueClosed:927326162861039626>"
    issue_not_planned = "<:IssueNotPlanned:1221831290895073421>"
    issue_draft = "<:IssueDraft:852596025147523102>"  # Not currently used by Github, but here for future.
    pull_request_open = "<:PROpen:852596471505223781>"
    pull_request_closed = "<:PRClosed:852596024732286976>"
    pull_request_draft = "<:PRDraft:852596025045680218>"
    pull_request_merged = "<:PRMerged:852596100301193227>"

    number_emojis = MappingProxyType(
        {
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
    )

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
    """URLs to commonly used icons."""

    questionmark = "https://cdn.discordapp.com/emojis/512367613339369475.png"
    bookmark = (
        "https://images-ext-2.discordapp.net/external/zl4oDwcmxUILY7sD9ZWE2fU5R7n6QcxEmPYSE5eddbg/"
        "%3Fv%3D1/https/cdn.discordapp.com/emojis/654080405988966419.png?width=20&height=20"
    )


class Month(enum.IntEnum):
    """Month of the year lookup. Used for in_month checks."""

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


class _Roles(EnvConfig, env_prefix="roles_"):
    owners: int = 267627879762755584
    admins: int = 267628507062992896
    moderation_team: int = 267629731250176001
    helpers: int = 267630620367257601
    core_developers: int = 587606783669829632
    everyone: int = Client.guild

    lovefest: int = 542431903886606399


Roles = _Roles()


class _Tokens(EnvConfig, env_prefix="tokens_"):
    giphy: SecretStr = ""
    youtube: SecretStr = ""
    tmdb: SecretStr = ""
    nasa: SecretStr = ""
    igdb_client_id: SecretStr = ""
    igdb_client_secret: SecretStr = ""
    github: SecretStr = ""
    unsplash: SecretStr = ""


Tokens = _Tokens()


class _Wolfram(EnvConfig, env_prefix="wolfram_"):
    user_limit_day: int = 10
    guild_limit_day: int = 67
    key: SecretStr = ""


Wolfram = _Wolfram()


class _Redis(EnvConfig, env_prefix="redis_"):
    host: str = "redis.databases.svc.cluster.local"
    port: int = 6379
    password: SecretStr = ""
    use_fakeredis: bool = False


Redis = _Redis()


class _Reddit(EnvConfig, env_prefix="reddit_"):
    subreddits: tuple[str, ...] = ("r/Python",)

    client_id: SecretStr = ""
    secret: SecretStr = ""
    webhook: int = 635408384794951680
    send_top_daily_posts: bool = True


Reddit = _Reddit()

# Default role combinations
MODERATION_ROLES = {Roles.moderation_team, Roles.admins, Roles.owners}
STAFF_ROLES = {Roles.helpers, Roles.moderation_team, Roles.admins, Roles.owners}

# Whitelisted channels
WHITELISTED_CHANNELS = (
    Channels.general,
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
    "Application bot.exe will be closed.",
    "Kernel Panic! *Kernel runs around in panic*",
    "Error 418. I am a teapot.",
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
    "I would love to, but unfortunately... no.",
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

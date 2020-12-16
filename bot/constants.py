import dataclasses
import enum
import logging
from datetime import datetime
from os import environ
from typing import Dict, NamedTuple

__all__ = (
    "AdventOfCode",
    "Branding",
    "Channels",
    "Client",
    "Colours",
    "Emojis",
    "Icons",
    "Lovefest",
    "Month",
    "Roles",
    "Tokens",
    "Wolfram",
    "RedisConfig",
    "MODERATION_ROLES",
    "STAFF_ROLES",
    "WHITELISTED_CHANNELS",
    "ERROR_REPLIES",
    "NEGATIVE_REPLIES",
    "POSITIVE_REPLIES",
)

log = logging.getLogger(__name__)


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
            log.info(f"Returning fallback cookie for board `{self.id}`.")
            return AdventOfCode.fallback_session

        return self._session


def _parse_aoc_leaderboard_env() -> Dict[str, AdventOfCodeLeaderboard]:
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
    year = int(environ.get("AOC_YEAR", datetime.utcnow().year))
    role_id = int(environ.get("AOC_ROLE_ID", 518565788744024082))


class Branding:
    cycle_frequency = int(environ.get("CYCLE_FREQUENCY", 3))  # 0: never, 1: every day, 2: every other day, ...


class Channels(NamedTuple):
    admins = 365960823622991872
    advent_of_code = int(environ.get("AOC_CHANNEL_ID", 782715290437943306))
    advent_of_code_commands = int(environ.get("AOC_COMMANDS_CHANNEL_ID", 607247579608121354))
    announcements = int(environ.get("CHANNEL_ANNOUNCEMENTS", 354619224620138496))
    big_brother_logs = 468507907357409333
    bot = 267659945086812160
    checkpoint_test = 422077681434099723
    devalerts = 460181980097675264
    devlog = int(environ.get("CHANNEL_DEVLOG", 622895325144940554))
    dev_contrib = 635950537262759947
    dev_branding = 753252897059373066
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
    community_bot_commands = int(environ.get("CHANNEL_COMMUNITY_BOT_COMMANDS", 607247579608121354))
    staff_lounge = 464905259261755392
    verification = 352442727016693763
    python_discussion = 267624335836053506
    hacktoberfest_2020 = 760857070781071431
    voice_chat = 412357430186344448

    # Core Dev Sprint channels
    sprint_announcements = 755958119963557958
    sprint_information = 753338352136224798
    sprint_organisers = 753340132639375420
    sprint_general = 753340631538991305
    sprint_social1_cheese_shop = 758779754789863514
    sprint_social2_pet_shop = 758780951978573824
    sprint_escape_room = 761031075942105109
    sprint_stdlib = 758553316732698634
    sprint_asyncio = 762904152438472714
    sprint_typing = 762904690341838888
    sprint_discussion_capi = 758553358587527218
    sprint_discussion_triage = 758553458365300746
    sprint_discussion_design = 758553492662255616
    sprint_discussion_mentor = 758553536623280159
    sprint_documentation = 761038271127093278


class Client(NamedTuple):
    name = "Sir Lancebot"
    guild = int(environ.get("BOT_GUILD", 267624335836053506))
    prefix = environ.get("PREFIX", ".")
    token = environ.get("BOT_TOKEN")
    sentry_dsn = environ.get("BOT_SENTRY_DSN")
    debug = environ.get("BOT_DEBUG", "").lower() == "true"
    github_bot_repo = "https://github.com/python-discord/sir-lancebot"
    # Override seasonal locks: 1 (January) to 12 (December)
    month_override = int(environ["MONTH_OVERRIDE"]) if "MONTH_OVERRIDE" in environ else None


class Colours:
    blue = 0x0279fd
    bright_green = 0x01d277
    dark_green = 0x1f8b4c
    orange = 0xe67e22
    pink = 0xcf84e0
    purple = 0xb734eb
    soft_green = 0x68c290
    soft_orange = 0xf9cb54
    soft_red = 0xcd6d6d
    yellow = 0xf9f586


class Emojis:
    star = "\u2B50"
    christmas_tree = "\U0001F384"
    check = "\u2611"
    envelope = "\U0001F4E8"
    trashcan = "<:trashcan:637136429717389331>"
    ok_hand = ":ok_hand:"

    dice_1 = "<:dice_1:755891608859443290>"
    dice_2 = "<:dice_2:755891608741740635>"
    dice_3 = "<:dice_3:755891608251138158>"
    dice_4 = "<:dice_4:755891607882039327>"
    dice_5 = "<:dice_5:755891608091885627>"
    dice_6 = "<:dice_6:755891607680843838>"

    issue = "<:IssueOpen:629695470327037963>"
    issue_closed = "<:IssueClosed:629695470570307614>"
    pull_request = "<:PROpen:629695470175780875>"
    pull_request_closed = "<:PRClosed:629695470519713818>"
    merge = "<:PRMerged:629695470570176522>"

    status_online = "<:status_online:470326272351010816>"
    status_idle = "<:status_idle:470326266625785866>"
    status_dnd = "<:status_dnd:470326272082313216>"
    status_offline = "<:status_offline:470326266537705472>"


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
    admin = int(environ.get("BOT_ADMIN_ROLE_ID", 267628507062992896))
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
    helpers = int(environ.get("ROLE_HELPERS", 267630620367257601))
    rockstars = 458226413825294336
    core_developers = 587606783669829632
    events_lead = 778361735739998228


class Tokens(NamedTuple):
    giphy = environ.get("GIPHY_TOKEN")
    omdb = environ.get("OMDB_API_KEY")
    youtube = environ.get("YOUTUBE_API_KEY")
    tmdb = environ.get("TMDB_API_KEY")
    nasa = environ.get("NASA_API_KEY")
    igdb = environ.get("IGDB_API_KEY")
    github = environ.get("GITHUB_TOKEN")


class Wolfram(NamedTuple):
    user_limit_day = int(environ.get("WOLFRAM_USER_LIMIT_DAY", 10))
    guild_limit_day = int(environ.get("WOLFRAM_GUILD_LIMIT_DAY", 67))
    key = environ.get("WOLFRAM_API_KEY")


class RedisConfig(NamedTuple):
    host = environ.get("REDIS_HOST", "redis.default.svc.cluster.local")
    port = environ.get("REDIS_PORT", 6379)
    password = environ.get("REDIS_PASSWORD")
    use_fakeredis = environ.get("USE_FAKEREDIS", "false").lower() == "true"


class Wikipedia:
    total_chance = 3


class Source:
    github = "https://github.com/python-discord/sir-lancebot"
    github_avatar_url = "https://avatars1.githubusercontent.com/u/9919"


# Default role combinations
MODERATION_ROLES = Roles.moderator, Roles.admin, Roles.owner
STAFF_ROLES = Roles.helpers, Roles.moderator, Roles.admin, Roles.owner

# Whitelisted channels
WHITELISTED_CHANNELS = (
    Channels.bot,
    Channels.community_bot_commands,
    Channels.off_topic_0,
    Channels.off_topic_1,
    Channels.off_topic_2,
    Channels.voice_chat,

    # Core Dev Sprint Channels
    Channels.sprint_announcements,
    Channels.sprint_information,
    Channels.sprint_organisers,
    Channels.sprint_general,
    Channels.sprint_social1_cheese_shop,
    Channels.sprint_social2_pet_shop,
    Channels.sprint_escape_room,
    Channels.sprint_stdlib,
    Channels.sprint_asyncio,
    Channels.sprint_typing,
    Channels.sprint_discussion_capi,
    Channels.sprint_discussion_triage,
    Channels.sprint_discussion_design,
    Channels.sprint_discussion_mentor,
    Channels.sprint_documentation,
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

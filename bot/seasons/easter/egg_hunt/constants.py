import os

from discord import Colour

from bot.constants import Channels, Client, bot


GUILD = bot.get_guild(Client.guild)


class EggHuntSettings:
    start_time = int(os.environ["HUNT_START"])
    end_time = start_time + 172800  # 48 hrs later
    windows = [int(w) for w in os.environ.get("HUNT_WINDOWS").split(',')] or []
    allowed_channels = [
        Channels.seasonalbot_chat,
        Channels.off_topic_0,
        Channels.off_topic_1,
        Channels.off_topic_2,
    ]


class Roles:
    white = GUILD.get_role(569304397054607363)
    blurple = GUILD.get_role(569304472820514816)


class Emoji:
    egg_white = bot.get_emoji(569266762428841989)
    egg_blurple = bot.get_emoji(569266666094067819)
    egg_gold = bot.get_emoji(569266900106739712)
    egg_diamond = bot.get_emoji(569266839738384384)


class Colours:
    white = Colour(0xFFFFFF)
    blurple = Colour(0x7289DA)
    gold = Colour(0xE4E415)
    diamond = Colour(0xECF5FF)

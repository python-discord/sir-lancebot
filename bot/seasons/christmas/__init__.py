from bot.constants import Colours
from bot.seasons import SeasonBase


class Christmas(SeasonBase):
    """
    We are getting into the festive spirit with a new server icon, new
    bot name and avatar, and some new commands for you to check out!

    No matter who you are, where you are or what beliefs you may follow,
    we hope every one of you enjoy this festive season!
    """
    name = "christmas"
    bot_name = "Merrybot"
    greeting = "Happy Holidays!"

    start_date = "01/12"
    end_date = "31/12"

    colour = Colours.dark_green
    icon = "/logos/logo_seasonal/christmas/festive.png"

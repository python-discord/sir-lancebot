from bot.constants import Colours, Month
from bot.seasons import SeasonBase


class Christmas(SeasonBase):
    """
    Christmas seasonal event attributes.

    We are getting into the festive spirit with a new server icon, new bot name and avatar, and some
    new commands for you to check out!

    No matter who you are, where you are or what beliefs you may follow, we hope every one of you
    enjoy this festive season!
    """

    season_name = "Festive season"
    bot_name = "Merrybot"

    colour = Colours.soft_red

    branding_path = "seasonal/christmas"

    months = {Month.december}

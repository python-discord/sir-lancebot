import datetime

from bot.constants import Colours
from bot.seasons import SeasonBase


class Christmas(SeasonBase):
    """
    Christmas seasonal event attributes.

    We are getting into the festive spirit with a new server icon, new bot name and avatar, and some
    new commands for you to check out!

    No matter who you are, where you are or what beliefs you may follow, we hope every one of you
    enjoy this festive season!
    """

    name = "christmas"
    bot_name = "Merrybot"
    greeting = "Happy Holidays!"

    start_date = "01/12"
    end_date = "01/01"

    colour = Colours.dark_green
    icon = (
        "/logos/logo_seasonal/christmas/2019/festive_512.gif",
    )

    @classmethod
    def end(cls) -> datetime.datetime:
        """Overload the `SeasonBase` method to account for the event ending in the next year."""
        return datetime.datetime.strptime(f"{cls.end_date}/{cls.current_year() + 1}", cls.date_format)

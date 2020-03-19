from bot.constants import Colours, Month
from bot.seasons import SeasonBase


class Wildcard(SeasonBase):
    """
    For the month of August, the season is a Wildcard.

    This docstring will not be used for announcements.
    Instead, we'll do the announcement manually, since
    it will change every year.

    This class needs slight changes every year,
    such as the bot_name, bot_icon and icon.

    IMPORTANT: DO NOT ADD ANY FEATURES TO THIS FOLDER.
               ALL WILDCARD FEATURES SHOULD BE ADDED
               TO THE EVERGREEN FOLDER!
    """

    season_name = "Wildcard"
    bot_name = "RetroBot"

    colour = Colours.purple

    months = {Month.august}

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

    name = "wildcard"
    bot_name = "RetroBot"

    # Duration of season
    start_date = "01/08"
    end_date = "01/09"

    # Season logo
    bot_icon = "/logos/logo_seasonal/retro_gaming/logo_8bit_indexed_504.png"
    icon = (
        "/logos/logo_seasonal/retro_gaming_animated/logo_spin_plain/logo_spin_plain_504.gif",
    )

from bot.constants import Colours
from bot.seasons import SeasonBase


class Easter(SeasonBase):
    """
    Easter is a beautiful time of the year often celebrated after the first Full Moon of the new spring season.
    This time is quite beautiful due to the colorful flowers coming out to greet us. So. let's greet Spring
    in an Easter celebration of contributions.
    """

    name = "easter"
    bot_name = "BunnyBot"
    greeting = "Happy Easter to us all!"

    # Duration of season
    start_date = "01/04"
    end_date = "30/04"

    colour = Colours.pink
    icon = "/logos/logo_seasonal/easter/easter.png"

from bot.constants import Colours
from bot.seasons import SeasonBase


class Halloween(SeasonBase):
    """
    Halloween Seasonal event attributes.

    Announcement for this cog temporarily disabled, since we're doing a custom
    Hacktoberfest announcement. If you're enabling the announcement again,
    make sure to update this docstring accordingly.
    """

    name = "halloween"
    bot_name = "NeonBot"
    greeting = "Happy Halloween!"

    start_date = "01/10"
    end_date = "01/11"

    colour = Colours.pink
    icon = (
        "/logos/logo_seasonal/hacktober/hacktoberfest.png",
    )

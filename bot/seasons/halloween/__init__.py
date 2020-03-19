from bot.constants import Colours, Month
from bot.seasons import SeasonBase


class Halloween(SeasonBase):
    """
    Halloween Seasonal event attributes.

    Announcement for this cog temporarily disabled, since we're doing a custom
    Hacktoberfest announcement. If you're enabling the announcement again,
    make sure to update this docstring accordingly.
    """

    season_name = "Halloween"
    bot_name = "NeonBot"

    colour = Colours.orange

    branding_path = "seasonal/halloween"

    months = {Month.october}

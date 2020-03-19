from bot.constants import Colours, Month
from bot.seasons import SeasonBase


class Christmas(SeasonBase):
    """Branding for december."""

    season_name = "Festive season"
    bot_name = "Merrybot"

    colour = Colours.soft_red
    description = (
        "The time is here to get into the festive spirit! No matter who you are, where you are, "
        "or what beliefs you may follow, we hope every one of you enjoy this festive season!"
    )

    branding_path = "seasonal/christmas"

    months = {Month.december}

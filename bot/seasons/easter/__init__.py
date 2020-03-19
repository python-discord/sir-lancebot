from bot.constants import Colours, Month
from bot.seasons import SeasonBase


class Easter(SeasonBase):
    """Branding for april."""

    season_name = "Easter"
    bot_name = "BunnyBot"

    colour = Colours.bright_green
    description = (
        "Bunny here, bunny there, bunny everywhere! Here at Python Discord, we celebrate "
        "our version of Easter during the entire month of April."
    )

    branding_path = "seasonal/easter"

    months = {Month.april}

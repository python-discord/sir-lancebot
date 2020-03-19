from bot.constants import Colours, Month
from bot.seasons import SeasonBase


class Valentines(SeasonBase):
    """Branding for february."""

    season_name = "Valentines"
    bot_name = "TenderBot"

    colour = Colours.pink
    description = "Love is in the air!"

    branding_path = "seasonal/valentines"

    months = {Month.february}

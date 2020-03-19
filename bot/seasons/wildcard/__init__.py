from bot.constants import Colours, Month
from bot.seasons import SeasonBase


class Wildcard(SeasonBase):
    """Branding for august."""

    season_name = "Wildcard"
    bot_name = "RetroBot"

    colour = Colours.purple
    description = "A season full of surprises!"

    months = {Month.august}

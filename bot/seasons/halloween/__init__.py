from bot.constants import Colours, Month
from bot.seasons import SeasonBase


class Halloween(SeasonBase):
    """Branding for october."""

    season_name = "Halloween"
    bot_name = "NeonBot"

    colour = Colours.orange
    description = "Trick or treat?!"

    branding_path = "seasonal/halloween"

    months = {Month.october}

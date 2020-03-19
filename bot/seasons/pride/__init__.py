from bot.constants import Colours, Month
from bot.seasons import SeasonBase


class Pride(SeasonBase):
    """Branding for june."""

    season_name = "Pride"
    bot_name = "ProudBot"

    colour = Colours.pink
    description = (
        "The month of June is a special month for us at Python Discord. It is very important to us "
        "that everyone feels welcome here, no matter their origin, identity or sexuality. During the "
        "month of June, while some of you are participating in Pride festivals across the world, "
        "we will be celebrating individuality and commemorating the history and challenges "
        "of the LGBTQ+ community with a Pride event of our own!"
    )

    branding_path = "seasonal/pride"

    months = {Month.june}

from bot.constants import Month
from bot.seasons import SeasonBase


class Valentines(SeasonBase):
    """
    Love is in the air! We've got a new icon and set of commands for the season of love.

    Get yourself into the bot-commands channel and check out the new features!
    """

    season_name = "Valentines"
    bot_name = "TenderBot"

    branding_path = "seasonal/valentines"

    months = {Month.february}

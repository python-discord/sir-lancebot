from bot.constants import Colours
from bot.seasons import SeasonBase


class Valentines(SeasonBase):
    """
    Love is in the air! We've got a new icon and set of commands for the season of love.

    Get yourself into the bot-commands channel and check out the new features!
    """
    name = "valentines"
    bot_name = "Tenderbot"
    greeting = "Get loved-up!"

    start_date = "01/02"
    end_date = "01/03"

    colour = Colours.pink
    icon = "/logos/logo_seasonal/valentines/loved_up.png"

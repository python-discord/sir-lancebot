from bot.constants import Colours
from bot.seasons import SeasonBase


class Halloween(SeasonBase):
    name = "halloween"
    bot_name = "Spookybot"
    greeting = "Happy Halloween!"

    start_date = "01/10"
    end_date = "31/10"

    colour = Colours.orange
    icon = "/logos/logo_seasonal/halloween/spooky.png"

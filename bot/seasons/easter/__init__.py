from bot.constants import Colours, Month
from bot.seasons import SeasonBase


class Easter(SeasonBase):
    """
    Here at Python Discord, we celebrate our version of Easter during the entire month of April.

    While this celebration takes place, you'll notice a few changes:

     • The server icon has changed to our Easter icon. Thanks to <@140605665772175361> for the
    design!

     • [Easter issues now available for SeasonalBot on the repo](https://git.io/fjkvQ).

     • You may see stuff like an Easter themed esoteric challenge, a celebration of Earth Day, or
    Easter-related micro-events for you to join. Stay tuned!

    If you'd like to contribute, head on over to <#635950537262759947> and we will help you get
    started. It doesn't matter if you're new to open source or Python, if you'd like to help, we
    will find you a task and teach you what you need to know.
    """

    season_name = "Easter"
    bot_name = "BunnyBot"

    colour = Colours.bright_green
    description = "Bunny here, bunny there, bunny everywhere!"

    branding_path = "seasonal/easter"

    months = {Month.april}

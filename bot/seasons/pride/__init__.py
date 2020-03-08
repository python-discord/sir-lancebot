from bot.constants import Month
from bot.seasons import SeasonBase


class Pride(SeasonBase):
    """
    The month of June is a special month for us at Python Discord.

    It is very important to us that everyone feels welcome here, no matter their origin,
    identity or sexuality. During the month of June, while some of you are participating in Pride
    festivals across the world, we will be celebrating individuality and commemorating the history
    and challenges of the LGBTQ+ community with a Pride event of our own!

    While this celebration takes place, you'll notice a few changes:
    • The server icon has changed to our Pride icon. Thanks to <@98694745760481280> for the design!
    • [Pride issues are now available for SeasonalBot on the repo](https://git.io/pythonpride).
    • You may see Pride-themed esoteric challenges and other microevents.

    If you'd like to contribute, head on over to <#635950537262759947> and we will help you get
    started. It doesn't matter if you're new to open source or Python, if you'd like to help, we
    will find you a task and teach you what you need to know.
    """

    season_name = "Pride"
    bot_name = "ProudBot"

    branding_path = "seasonal/pride"

    months = {Month.june}

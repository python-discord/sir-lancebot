from bot.seasons import SeasonBase


class Pride(SeasonBase):
    """
    No matter your origin, identity or sexuality, we come together to celebrate each and everyone's individuality.
    Feature contributions to ProudBot is encouraged to commemorate the history and challenges of the LGBTQ+ community.
    Happy Pride Month
    """

    name = "pride"
    bot_name = "ProudBot"
    greeting = "Happy Pride Month!"

    # Duration of season
    start_date = "01/06"
    end_date = "30/06"

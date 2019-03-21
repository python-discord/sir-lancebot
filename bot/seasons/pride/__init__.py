from bot.seasons import SeasonBase

class Pride(SeasonBase):
    """
    No matter your origins, identity or sexuality, we hope we can come together to celebrate each and every person's individuality this Pride Month.
    Features of ProudBot will be encouraged to be contributed during this event which appropriately commemorate the history and challenges of the LGBTQ+ community.
    """

    name = "pride"
    bot_name = "ProudBot"
    greeting = "Happy Pride Month!"

    # Duration of season
    start_date = "01/06"
    end_date = "30/06"

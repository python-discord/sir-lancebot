from bot.seasons import SeasonBase

class Pride(SeasonBase):
    """
    In support of all cultures and communities, and in hopes of providing global cultural knowledge,
    this event provides information about the LGBTQ community.
    """

    name = "pride"
    bot_name = "ProudBot"
    greeting = "Happy Pride Month!"

    # Duration of season
    start_date = "01/06"
    end_date = "30/06"

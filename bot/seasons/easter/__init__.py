from bot.seasons import SeasonBase


class Easter(SeasonBase):
    """
    Easter is a beautiful time of the year often celebrated after the first full moon of the
    Northern Hemisphere's new spring season, making it a beautiful time of the year with colorful
    flowers coming out to greet us.

    To celebrate, we have a lovely new colourful server icon. Thanks to <@140605665772175361> for
    the design.

    We hope you can join us in the spring and Easter celebrations by heading over to the
    [SeasonalBot GitHub repo](https://git.io/fjkvQ) and either submit some issues with ideas for
    commands for this season, or to pick out an issue that you think looks fun to work on yourself.

    Come over to <#542272993192050698> if you're interested or have any questions!
    """

    name = "easter"
    bot_name = "BunnyBot"
    greeting = "Happy Easter!"

    # Duration of season
    start_date = "01/04"
    end_date = "30/04"

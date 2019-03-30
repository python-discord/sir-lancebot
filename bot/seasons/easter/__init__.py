from bot.seasons import SeasonBase


class Easter(SeasonBase):
    """
    To celebrate, we have a lovely new colourful server icon. Thanks to <@140605665772175361> for
    the design.

    Easter is a beautiful time of the year often celebrated after the first Full Moon of the
    Northern Hemisphere's new spring seasonm, making it a beautiful time of the year with colorful
    flowers coming out to greet us.

    We hope you can join us in the Spring and Easter celebrations by heading over to the
    [SeasonalBot GitHub repo](https://git.io/fjkvQ) and either submit some issues with ideas for
    commands of this season, or to pick out an issue that you think looks fun to build yourself.

    Come over to <#542272993192050698> if you're interested or had any questions!
    """

    name = "easter"
    bot_name = "BunnyBot"
    greeting = "Happy Easter!"

    # Duration of season
    start_date = "01/04"
    end_date = "30/04"

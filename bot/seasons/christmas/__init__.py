from bot.seasons import SeasonBase


class Christmas(SeasonBase):
    name = "christmas"
    start_date = "01/12"
    end_date = "31/12"
    bot_name = "Santabot"

    def __init__(self, bot):
        self.bot = bot

    @property
    def bot_avatar(self):
        with open(self.avatar_path("christmas.png"), "rb") as avatar:
            return bytearray(avatar.read())

from bot.seasons import SeasonBase


class Christmas(SeasonBase):
    name = "christmas"

    def __init__(self, bot):
        self.bot = bot
        self.start_date = "01/12"
        self.end_date = "31/12"
        self.bot_name = "Santabot"

        super().__init__()

    @property
    def bot_avatar(self):
        with open(self.avatar_path("christmas.png"), "rb") as avatar:
            return bytearray(avatar.read())

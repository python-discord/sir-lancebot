from bot.seasons import SeasonBase


class Halloween(SeasonBase):
    name = "halloween"

    def __init__(self, bot):
        self.bot = bot
        self.start_date = "01/10"
        self.end_date = "31/10"
        self.bot_name = "Spookybot"

        super().__init__()

    @property
    def bot_avatar(self):
        with open(self.avatar_path("spooky.png"), "rb") as avatar:
            return bytearray(avatar.read())

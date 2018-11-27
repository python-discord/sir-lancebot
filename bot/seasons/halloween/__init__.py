from bot.seasons import SeasonBase


class Halloween(SeasonBase):
    name = "halloween"
    start_date = "01/10"
    end_date = "31/10"
    bot_name = "Spookybot"

    def __init__(self, bot):
        self.bot = bot

    @property
    def bot_avatar(self):
        with open(self.avatar_path("spooky.png"), "rb") as avatar:
            return bytearray(avatar.read())

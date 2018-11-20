from bot.seasons import SeasonBase


class Evergreen(SeasonBase):
    def __init__(self, bot):
        self.bot = bot
        self.bot_name = "SeasonalBot"

    @property
    def bot_avatar(self):
        with open(self.avatar_path("standard.png"), "rb") as avatar:
            return bytearray(avatar.read())

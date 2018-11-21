from bot.seasons import SeasonBase


class Evergreen(SeasonBase):
    bot_name = "SeasonalBot"

    def __init__(self, bot):
        self.bot = bot

    @property
    def bot_avatar(self):
        with open(self.avatar_path("standard.png"), "rb") as avatar:
            return bytearray(avatar.read())

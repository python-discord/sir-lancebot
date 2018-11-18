from .season import Season


class Evergreen(Season):
    def __init__(self, bot):
        self.bot = bot
        self.bot_name = "SeasonalBot"

        with open("bot/resources/avatars/standard.png", "rb") as avatar:
            self.bot_avatar = bytearray(avatar.read())

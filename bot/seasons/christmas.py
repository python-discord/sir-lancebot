from .season import Season


class Christmas(Season):
    name = "christmas"

    def __init__(self, bot):
        self.bot = bot
        self.start_string = "01/12"
        self.end_string = "31/12"
        self.bot_name = "Santabot"

        with open("bot/resources/avatars/christmas.png", "rb") as avatar:
            self.bot_avatar = bytearray(avatar.read())

        super().__init__()

from .season import Season


class Halloween(Season):
    name = "halloween"

    def __init__(self, bot):
        self.bot = bot
        self.start_string = "01/10"
        self.end_string = "31/10"
        self.bot_name = "Spookybot"

        with open("bot/resources/avatars/spooky.png", "rb") as avatar:
            self.bot_avatar = bytearray(avatar.read())

        super().__init__()

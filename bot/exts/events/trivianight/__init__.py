class UserScore:
    """Marker class for passing into the scoreboard to add points/record speed."""

    __slots__ = ("user_id",)

    def __init__(self, user_id: int):
        self.user_id = user_id

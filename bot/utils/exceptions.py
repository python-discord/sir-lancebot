
class UserNotPlayingError(Exception):
    """Raised when users try to use game commands when they are not playing."""

    pass


class ExternalAPIError(Exception):
    """Raised when an external API(eg. Wikipedia) returns an error."""

    def __init__(self, api: str):
        super().__init__()
        self.api = api
    pass

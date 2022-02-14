from typing import Optional


class UserNotPlayingError(Exception):
    """Raised when users try to use game commands when they are not playing."""

    pass


class APIError(Exception):
    """Raised when an external API (eg. Wikipedia) returns an error response."""

    def __init__(self, api: str, status_code: int, error_msg: Optional[str] = None):
        super().__init__()
        self.api = api
        self.status_code = status_code
        self.error_msg = error_msg


class MovedCommandError(Exception):
    """Raised when a command has moved locations."""

    def __init__(self, new_command_name: str):
        self.new_command_name = new_command_name

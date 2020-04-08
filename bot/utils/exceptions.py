class BrandingError(Exception):
    """Exception raised by the BrandingManager cog."""

    pass


class UserNotPlayingError(Exception):
    """Will raised when user try to use game commands when not playing."""

    pass

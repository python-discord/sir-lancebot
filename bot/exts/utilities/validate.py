import re
from datetime import UTC, datetime


class GitHubStatsValidate:
    """Class providing validation methods for GitHub repository and date formats."""

    def validate_repo_format(self, repo_str: str) -> bool:
        """Validates that the repo is in the format owner/repo. Githubinfo has its own check so wont be used."""
        # Part one can be any char except a "/" followed by a "/" followed by any char except a "/"
        pattern = r"^[^/]+/[^/]+$"
        return bool(re.match(pattern, repo_str))

    # Went with only ISO standard. Have to change the tests.
    def validate_date_format(self, date_str: str) -> bool:
        """Validates that the date string is formatted correctly."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
            return True
        except ValueError:
            return False


    # Validates that the given dates are in order and that they are
    # logically valid.
    def validate_date_range(self, start_date: str, end_date: str) -> bool:
        """Validates the given date range."""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=UTC)
            end = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            return False

        time_now = datetime.now(UTC)

        if start > end:
            return False

        return not end > time_now

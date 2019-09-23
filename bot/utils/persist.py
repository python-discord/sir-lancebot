import sqlite3
from pathlib import Path
from shutil import copyfile

from bot.seasons.season import get_seasons

DIRECTORY = Path("data")  # directory that has a persistent volume mapped to it


def make_persistent(file_path: Path) -> Path:
    """
    Copy datafile at the provided file_path to the persistent data directory.

    A persistent data file is needed by some features in order to not lose data
    after bot rebuilds.

    This function will ensure that a clean data file with default schema,
    structure or data is copied over to the persistent volume before returning
    the path to this new persistent version of the file.

    If the persistent file already exists, it won't be overwritten with the
    clean default file, just returning the Path instead to the existing file.

    Note: Avoid using the same file name as other features in the same seasons
    as otherwise only one datafile can be persistent and will be returned for
    both cases.

    Example Usage:
    >>> import json
    >>> template_datafile = Path("bot", "resources", "evergreen", "myfile.json")
    >>> path_to_persistent_file = make_persistent(template_datafile)
    >>> print(path_to_persistent_file)
    data/evergreen/myfile.json
    >>> with path_to_persistent_file.open("w+") as f:
    >>>     data = json.load(f)
    """
    # ensure the persistent data directory exists
    if not DIRECTORY.exists():
        DIRECTORY.mkdir()

    if not file_path.is_file():
        raise OSError(f"File not found at {file_path}.")

    # detect season in datafile path for assigning to subdirectory
    season = next((s for s in get_seasons() if s in file_path.parts), None)

    if season:
        # make sure subdirectory exists first
        subdirectory = Path(DIRECTORY, season)
        if not subdirectory.exists():
            subdirectory.mkdir()

        persistent_path = Path(subdirectory, file_path.name)

    else:
        persistent_path = Path(DIRECTORY, file_path.name)

    # copy base/template datafile to persistent directory
    if not persistent_path.exists():
        copyfile(file_path, persistent_path)

    return persistent_path


def sqlite(db_path: Path) -> sqlite3.Connection:
    """Copy sqlite file to the persistent data directory and return an open connection."""
    persistent_path = make_persistent(db_path)
    return sqlite3.connect(persistent_path)

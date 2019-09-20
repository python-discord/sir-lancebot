import sqlite3
from pathlib import Path
from shutil import copyfile

DIRECTORY = Path("data")  # directory that has a persistent volume mapped to it


def datafile(file_path: Path) -> Path:
    """
    Copy datafile at the provided file_path to the persistent data directory.

    A persistent data file is needed by some features in order to not lose data
    after bot rebuilds.

    This function will ensure that a clean data file with default schema,
    structure or data is copied over to the persistent volume before returning
    the path to this new persistent version of the file.

    If the persistent file already exists, it won't be overwritten with the
    clean default file, just returning the Path instead to the existing file.

    Example Usage:
    >>> clean_default_datafile = Path("bot", "resources", "datafile.json")
    >>> persistent_file_path = datafile(clean_default_datafile)
    """
    if not file_path.exists():
        raise OSError(f"File not found at {file_path}.")

    persistant_path = Path(DIRECTORY, file_path.name)

    if not persistant_path.exists():
        copyfile(file_path, persistant_path)

    return persistant_path


def sqlite(db_path: Path) -> sqlite3.Connection:
    """Copy sqlite file to the persistent data directory and return an open connection."""
    persistant_path = datafile(db_path)
    return sqlite3.connect(persistant_path)

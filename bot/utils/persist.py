import sqlite3
from pathlib import Path
from shutil import copyfile

DIRECTORY = Path("data")  # directory that has a persistent volume mapped to it


def datafile(file_path: Path) -> Path:
    """Copy datafile at the provided file_path to the persistent data directory."""
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

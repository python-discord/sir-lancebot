import tarfile
import typing
import zipfile
from io import BytesIO
from pathlib import PurePath


def _tar_retrieve_file(archive_data: typing.BinaryIO, filename: str) -> bytes:
    with tarfile.open(fileobj=archive_data) as arc:
        for el in arc.getmembers():
            if PurePath(el.name).name == filename:
                fo = arc.extractfile(el)
                if fo is None:
                    raise ValueError(
                        "Member has the right name but couldn't extract:", el
                    )
                return fo.read()
    raise FileNotFoundError("No member with this name was found in archive:", filename)


def _zip_retrieve_file(archive_data: typing.BinaryIO, filename: str) -> bytes:
    with zipfile.ZipFile(file=archive_data) as arc:
        for el in arc.filelist:
            if PurePath(el.filename).name == filename:
                return arc.read(el)
    raise FileNotFoundError("No member with this name was found in archive:", filename)


def archive_retrieve_file(
    archive_data: bytes | typing.BinaryIO, filename: str
) -> bytes:
    """Retrieves a single file by filename (not by full path) from a tar or zip archive in memory."""
    if isinstance(archive_data, bytes | bytearray | memoryview):
        archive_data = BytesIO(archive_data)
    if tarfile.is_tarfile(archive_data):
        return _tar_retrieve_file(archive_data, filename)
    try:
        return _zip_retrieve_file(archive_data, filename)
    except zipfile.BadZipFile as e:
        if "File is not a zip file" in str(e):
            raise ValueError(
                "Archive unsupported: was neither a valid tarfile nor a valid zipfile"
            )
        raise

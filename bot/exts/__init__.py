import pkgutil
from collections.abc import Iterator

from pydis_core.utils.logging import get_logger

__all__ = ("get_package_names",)

log = get_logger(__name__)


def get_package_names() -> Iterator[str]:
    """Iterate names of all packages located in /bot/exts/."""
    for package in pkgutil.iter_modules(__path__):
        if package.ispkg:
            yield package.name

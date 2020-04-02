import logging
import pkgutil
from pathlib import Path
from typing import Iterator

__all__ = ("get_package_names", "walk_extensions")

log = logging.getLogger(__name__)


def get_package_names() -> Iterator[str]:
    """Iterate names of all packages located in /bot/exts/."""
    for package in pkgutil.iter_modules(__path__):
        if package.ispkg:
            yield package.name


def walk_extensions() -> Iterator[str]:
    """
    Iterate dot-separated paths to all extensions.

    The strings are formatted in a way such that the bot's `load_extension`
    method can take them. Use this to load all available extensions.

    This intentionally doesn't make use of pkgutil's `walk_packages`, as we only
    want to build paths to extensions - not recursively all modules. For some
    extensions, the `setup` function is in the package's __init__ file, while
    modules nested under the package are only helpers. Constructing the paths
    ourselves serves our purpose better.
    """
    base_path = Path(__path__[0])

    for package in get_package_names():
        for extension in pkgutil.iter_modules([base_path.joinpath(package)]):
            yield f"bot.exts.{package}.{extension.name}"

import resource
import warnings
from collections.abc import Iterator
from contextlib import contextmanager, nullcontext
from multiprocessing import parent_process
from pathlib import Path
from typing import Literal


@contextmanager
def rlimit_context(
    resource_id: int, soft_value: int | None = None, hard_value: int | None = None
) -> Iterator[None]:
    """
    Context manager to temporarily set an rlimit to a value and restore it on exit.

    A value of None for one of the limits means that the current value will be used.
    This should typically be used in a subprocess, and will emit a warning if used from the main process.
    """
    if soft_value is None and hard_value is None:
        warnings.warn(
            "rlimit_context does nothing if both soft_value and hard_value are None",
            stacklevel=2,
        )
    if parent_process() is None:
        warnings.warn("rlimit_context used from main process", stacklevel=2)

    old_soft, old_hard = resource.getrlimit(resource_id)
    new_soft, new_hard = old_soft, old_hard
    if soft_value is not None:
        new_soft = soft_value
    if hard_value is not None:
        new_hard = hard_value

    resource.setrlimit(resource_id, (new_soft, new_hard))
    try:
        yield
    finally:
        resource.setrlimit(resource_id, (old_soft, old_hard))


def render_typst_worker(
    source_path: Path,
    format: Literal["pdf", "svg", "png"] = "png",
    ppi: float | None = None,
    mem_rlimit: int | None = None,
) -> bytes:
    """
    Renders Typst from source to output.

    Uses the source path's parent as the typst root path.
    Intended to be ran in a subprocess for concurrency and timeouts.
    """
    import typst

    ctx = (
        rlimit_context(resource.RLIMIT_AS, soft_value=mem_rlimit)
        if mem_rlimit is not None
        else nullcontext()
    )
    with ctx:
        res = typst.compile(
            source_path, format=format, root=source_path.parent, ppi=ppi
        )
    return res

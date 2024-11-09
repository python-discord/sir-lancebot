import asyncio.subprocess
import contextlib
import resource
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from subprocess import CalledProcessError
from typing import Literal

from bot.constants import Typst as Config


def _set_limits(mem_rlimit: int | None = None) -> None:
    if mem_rlimit is not None:
        resource.setrlimit(resource.RLIMIT_AS, (mem_rlimit, -1))


@dataclass
class TypstCompileResult:
    """Result of Typst compilation."""

    output: bytes
    stderr: bytes


async def compile_typst(
    source: str,
    root_path: Path,
    format: Literal["pdf", "svg", "png"] = "png",
    ppi: float | None = None,
    mem_rlimit: int | None = None,
    jobs: int | None = None,
) -> TypstCompileResult:
    """
    Renders Typst in a subprocess.

    Since malicious Typst source can take arbitrary resources to compile,
    this should be ran with a timeout, and ideally a `mem_rlimit`.
    `root_path` should be a path to a directory where all the files (if any)
    that should be accessible are placed.

    """
    typst_path = Path(Config.typst_path).resolve()
    if not typst_path.exists():
        raise ValueError("Typst executable was not found at path", typst_path)
    if not root_path.is_dir():
        raise ValueError("Root directory was not a directory", root_path)

    args = [
        "compile",
        "--root",
        root_path,
        "--format",
        format,
    ]
    if ppi is not None:
        args += ["--ppi", str(ppi)]
    if jobs is not None:
        args += ["--jobs", str(jobs)]
    # input and output from CLI
    args += ["-", "-"]

    try:
        proc = await asyncio.subprocess.create_subprocess_exec(
            typst_path,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=partial(_set_limits, mem_rlimit=mem_rlimit),
        )

        stdout, stderr = await proc.communicate(input=source.encode("utf-8"))
        if proc.returncode is None:
            # shouldn't be possible
            raise RuntimeError("Process didn't terminate after communicate")
        if proc.returncode != 0:
            raise CalledProcessError(
                proc.returncode, [typst_path, *args], stdout, stderr
            )
    # if the task is cancelled or any other problem happens, make sure to kill the worker if it still exists
    except BaseException:
        with contextlib.suppress(UnboundLocalError, ProcessLookupError):
            proc.kill()
        raise
    return TypstCompileResult(output=stdout, stderr=stderr)

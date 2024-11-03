from pathlib import Path


def render_typst_worker(source_path: Path, output_path: Path, ppi: float | None = None) -> None:
    """
    Renders Typst from source to output.

    Uses the source path's parent as the typst root path.
    Intended to be ran in a subprocess for concurrency and timeouts.
    """
    import typst

    typst.compile(source_path, output_path, root=source_path.parent, ppi=ppi)

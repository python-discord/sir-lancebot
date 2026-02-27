from datetime import datetime, timedelta
from pathlib import Path

from bot.exts.fun.mathdoku_parser import create_grids


def _load_5x5_grid(tmp_path: Path) -> None:
    """Creates a temp file with a valid grid in it and attempts to load a valid grid from that file."""
    content = """\
5x5:d5 (easy)
FFFF5
AAE1B
CCEGB
CDIGG
3DIHH

A 7+
B 2-
C 9+
D 5+
E 2/
F 10+
G 40x
H 2/
I 2-

4 2 1 3 5
2 5 4 1 3
5 3 2 4 1
1 4 3 5 2
3 1 5 2 4
"""
    grids_file = tmp_path / "grids.txt"
    grids_file.write_text(content, encoding="utf-8")
    grids = create_grids(file_path=grids_file)

    grid = grids[5]["easy"][0]

    return grid

def _test_hint_find_first_empty_cell(tmp_path: Path) -> None:
    grid = _load_5x5_grid(tmp_path)

    result = grid.hint(now=datetime(2026, 2, 25, 14, 0, 0))

    assert result["type"] == "hint"
    assert result["row"] == 0
    assert result["column"] == 0
    assert result["value"] == 4

def _test_hint_find_empty_cell_after_some_filled(tmp_path: Path) -> None:
    grid = _load_5x5_grid(tmp_path)

    grid.cells[0][0].guess = 4
    grid.cells[0][1].guess = 2
    grid.cells[0][2].guess = 1

    result = grid.hint(now=datetime(2026, 2, 25, 14, 0, 0))

    assert result["type"] == "hint"
    assert result["row"] == 0
    assert result["column"] == 3
    assert result["value"] == 3


def test_hint_cooldown(tmp_path: Path) -> None:
    grid = _load_5x5_grid(tmp_path)
    t0 = datetime(2026, 2, 25, 14, 0, 0)
    grid.hint(now=t0)

    result = grid.hint(now=t0 + timedelta(seconds=30))

    assert result["type"] == "cooldown"
    assert result["remaining_seconds"] == 150


def test_hint_available_again_at_180_seconds(tmp_path: Path) -> None:
    grid = _load_5x5_grid(tmp_path)
    t0 = datetime(2026, 2, 25, 14, 0, 0)

    first_hint = grid.hint(now=t0)
    second_hint = grid.hint(now=t0 + timedelta(seconds=180))

    assert first_hint["type"] == "hint"
    assert second_hint["type"] == "hint"


def test_hint_all_cells_filled(tmp_path: Path) -> None:
    grid = _load_5x5_grid(tmp_path)

    for row in grid.cells:
        for cell in row:
            cell.guess = cell.correct

    result = grid.hint(now=datetime(2026, 2, 25, 14, 0, 0))

    assert result["type"] == "all filled cells"

from pathlib import Path

from bot.exts.fun.mathdoku import Block
from bot.exts.fun.mathdoku_parser import create_grids


VALID_CONTENT = """\
5x5:d5
.KK "1:(d=5)"
EAACC
EB3CG
EBF5G
E1FDD
FFFD5

A 1-
B 6+
C 12x
D 8+
E 30x
F 15+
G 3-

1 5 4 3 2
5 4 3 2 1
3 2 1 5 4
2 1 5 4 3
4 3 2 1 5
"""


def test_load_valid_5x5_grid(tmp_path: Path) -> None:
    """Creates a temp file with a valid grid in it and attempts to load a valid grid from that file."""
    grids_file = tmp_path / "grids.txt"
    grids_file.write_text(VALID_CONTENT, encoding="utf-8")

    grids = create_grids(file_path=grids_file)

    assert len(grids) == 1
    grid = grids[0]
    assert grid.size == 5
    assert len(grid.blocks) == 11
    assert grid.cells[0][0].correct == 1
    assert grid.cells[0][0].block.id == "E"
    assert grid.cells[0][0].block.operation == "x"
    assert grid.cells[0][0].block.number == 30

    assert grid.cells[4][4].correct == 5
    assert type(grid.cells[4][4].block) is Block


def test_load_invalid_5x5_grid(tmp_path: Path) -> None:
    """Creates a temp file with an invalid grid in it and attempts to load a grid from that file."""
    content = """\
5x5:d5
.KK "1:(d=5)"
EAACC
EB3C
EBF5G
E1FDD
FFFD5

A 1-
B 6+
C 12x
D 8+
E 30x
F 15+
G 3-

1 5 4 3 2
5 4 3 2 1
3 2 1 5 4
2 1 5 4 3
4 3 2 1 5
"""
    grids_file = tmp_path / "grids.txt"
    grids_file.write_text(content, encoding="utf-8")

    grids = create_grids(file_path=grids_file)

    assert len(grids) == 0


def test_load_valid_5x5_grid_and_check_singletons_have_blocks(tmp_path: Path) -> None:
    """Loads a grid and checks that singleton cells have blocks that have correct numbers."""
    grids_file = tmp_path / "grids.txt"
    grids_file.write_text(VALID_CONTENT, encoding="utf-8")

    grids = create_grids(file_path=grids_file)
    grid = grids[0]
    assert type(grid[2][3].block) is Block
    assert type(grid[2][3].block.number) is int


def test_load_valid_5x5_grid_and_check_singleton_blocks_have_cells(tmp_path: Path) -> None:
    """Loads a grid and checks that singleton cells have blocks that contain a list with only them."""
    grids_file = tmp_path / "grids.txt"
    grids_file.write_text(VALID_CONTENT, encoding="utf-8")

    grids = create_grids(file_path=grids_file)
    grid = grids[0]
    cell = grid[2][3]
    block = cell.block
    assert len(block.cells) == 1
    assert block.cells[0] is cell

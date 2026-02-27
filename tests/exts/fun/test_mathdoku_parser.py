from pathlib import Path

from bot.exts.fun.mathdoku import Block
from bot.exts.fun.mathdoku_parser import create_grids

VALID_5x5 = """\
5x5:d5 (easy)
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

VALID_9x9 = """\
9x9:d6 (easy)
TTbbVCKKF
eMbNVCK7F
eMWNVRRd9
QEWBLLRdJ
QEfBaaDDJ
YOfGSaIIZ
YOOGS6hhZ
gPPA6HHUU
gP7AXXccc

A 14+
B 2-
C 4-
D 54x
E 2-
F 5-
G 6x
H 5-
I 5+
J 15x
K 108x
L 10+
M 1-
N 1-
O 288x
P 17+
Q 2/
R 168x
S 8-
T 35x
U 3-
V 13+
W 4-
X 36x
Y 13+
Z 1-
a 11+
b 9+
c 15+
d 3/
e 72x
f 11+
g 2-
h 3-

5 7 2 1 8 4 9 3 6
9 2 6 5 3 8 4 7 1
8 1 5 4 2 7 3 6 9
4 6 1 9 7 3 8 2 5
2 4 8 7 5 1 6 9 3
6 8 3 2 9 5 1 4 7
7 9 4 3 1 6 2 5 8
3 5 9 8 6 2 7 1 4
1 3 7 6 4 9 5 8 2
"""

VALID_5x5_DOUBLE_DIGIT_DIFFICULTY = """\
5x5:d12 (hard)
EIIAA
ECCDA
JJCDD
HBBFF
HHGGF

A 15x
B 6+
C 40x
D 11+
E 5+
F 24x
G 5+
H 10+
I 1-
J 4+

4 2 3 5 1
1 4 5 2 3
3 1 2 4 5
2 5 1 3 4
5 3 4 1 2
"""


def test_load_valid_5x5_grid(tmp_path: Path) -> None:
    """Creates a temp file with a valid grid in it and attempts to load a valid grid from that file."""
    grids_file = tmp_path / "grids.txt"
    grids_file.write_text(VALID_5x5, encoding="utf-8")

    grids = create_grids(file_path=grids_file)

    assert len(grids) == 1
    grid = grids[5]["easy"][0]
    assert grid.difficulty == "easy"
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
5x5:d5 (easy)
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
    grids_file.write_text(VALID_5x5, encoding="utf-8")

    grids = create_grids(file_path=grids_file)
    grid = grids[5]["easy"][0]
    assert type(grid[2][3].block) is Block
    assert type(grid[2][3].block.number) is int


def test_load_valid_5x5_grid_and_check_singleton_blocks_have_cells(tmp_path: Path) -> None:
    """Loads a grid and checks that singleton cells have blocks that contain a list with only them."""
    grids_file = tmp_path / "grids.txt"
    grids_file.write_text(VALID_5x5, encoding="utf-8")

    grids = create_grids(file_path=grids_file)
    grid = grids[5]["easy"][0]
    cell = grid[2][3]
    block = cell.block
    assert len(block.cells) == 1
    assert block.cells[0] is cell


def test_load_valid_5x5_with_double_digit_difficulty(tmp_path: Path) -> None:
    """Loads a grid with a double digit difficulty and checks that it was loaded."""
    grids_file = tmp_path / "grids.txt"
    grids_file.write_text(VALID_5x5_DOUBLE_DIGIT_DIFFICULTY, encoding="utf-8")

    grids = create_grids(file_path=grids_file)

    assert len(grids) == 1
    grid = grids[5]["hard"][0]
    assert grid.difficulty == "hard"
    assert grid.size == 5
    assert len(grid.blocks) == 10
    assert grid.cells[0][1].correct == 2
    assert grid.cells[0][1].block.id == "I"
    assert grid.cells[0][1].block.operation == "-"
    assert grid.cells[0][1].block.number == 1

    assert grid.cells[4][3].correct == 1


def test_load_valid_9x9(tmp_path: Path) -> None:
    """Loads a 9x9 grid and checks that it was loaded correctly."""
    grids_file = tmp_path / "grids.txt"
    grids_file.write_text(VALID_9x9, encoding="utf-8")

    grids = create_grids(file_path=grids_file)

    assert len(grids) == 1
    grid = grids[9]["easy"][0]
    assert grid.difficulty == "easy"
    assert grid.size == 9
    assert len(grid.blocks) == 39
    assert grid.cells[0][1].correct == 7
    assert grid.cells[0][1].block.id == "T"
    assert grid.cells[0][1].block.operation == "x"
    assert grid.cells[0][1].block.number == 35

    assert grid.cells[4][3].correct == 7

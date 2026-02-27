from pathlib import Path

from bot.exts.fun.mathdoku_parser import create_grids


def test_victory_check_won(tmp_path: Path) -> None:
    """Creates a temp file with a valid grid in it and attempts to load a valid grid from that file."""
    content = """\
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
    grids_file = tmp_path / "grids.txt"
    grids_file.write_text(content, encoding="utf-8")

    grids = create_grids(file_path=grids_file)

    grid = grids[5]["easy"][0]

    # Set guess to possible solution
    for row in grid.cells:
        for cell in row:
            cell.guess = cell.correct

    assert grid.check_victory()


def test_victory_check_lost(tmp_path: Path) -> None:
    """Creates a temp file with a valid grid in it and attempts to load a valid grid from that file."""
    content = """\
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
    grids_file = tmp_path / "grids.txt"
    grids_file.write_text(content, encoding="utf-8")

    grids = create_grids(file_path=grids_file)

    grid = grids[5]["easy"][0]

    # Set guess to possible solution
    for row in grid.cells:
        for cell in row:
            cell.guess = cell.correct

    grid.cells[0][1].guess = 4

    assert grid.check_victory() is False

    assert grid._latin_square_check() is False

    assert grid._blocks_fufilled_check()[0].id == "A"


def test_victory_check_won_with_division(tmp_path: Path) -> None:
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

    # Set guess to possible solution
    for row in grid.cells:
        for cell in row:
            cell.guess = cell.correct

    assert grid.check_victory()


def test_victory_check_lost_with_division(tmp_path: Path) -> None:
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

    # Set guess to possible solution
    for row in grid.cells:
        for cell in row:
            cell.guess = cell.correct

    grid.cells[4][4].guess = 2

    assert grid.check_victory() is False

    assert grid._latin_square_check() is False

    assert grid._blocks_fufilled_check()[0].id == "H"

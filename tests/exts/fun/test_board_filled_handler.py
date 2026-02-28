from pathlib import Path

from bot.exts.fun.mathdoku_parser import create_grids


def test_board_filled_handler(tmp_path: Path) -> None:
    """
    Contract: The board filled should color in the right and wrong blocks
    and save the board to testdokuboardfilled2.png.
    """
    filepath = "testdokuboardfilled2.png"

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
    grid.cells[0][0].guess = 1

    # Comment out the line below to see different colors for singletons
    assert grid._latin_square_check() is False
    assert grid.check_victory() is False
    assert grid.board_filled_handler() is False

    assert grid._blocks_fufilled_check()[0].id == "F"
    assert grid._blocks_fufilled_check()[1].id == "H"

    grid._generate_image(outfile=filepath, saveToFile=False)


def _test_board_filled_handler3x3(tmp_path: Path) -> None:
    """
    Contract: The board filled should color in the right and wrong blocks
    and save the board to testdokuboardfilled3.png.
    """
    filepath = "testdokuboardfilled3.png"

    content = """\
3x3:d3 (easy)
AAB
CDB
CEE

A 3+
B 4+
C 6x
D 3 
E 1-

1 2 3 
2 3 1
3 1 2 
"""
    grids_file = tmp_path / "grids.txt"
    grids_file.write_text(content, encoding="utf-8")

    grids = create_grids(file_path=grids_file)

    grid = grids[3]["easy"][0]

    # Set guess to possible solution
    for row in grid.cells:
        for cell in row:
            cell.guess = cell.correct

    # Comment out the line below to see different colors for singletons
    assert grid._latin_square_check() is False
    assert grid.check_victory() is False
    assert grid.board_filled_handler() is False

    assert grid._blocks_fufilled_check()[0].id == "F"
    assert grid._blocks_fufilled_check()[1].id == "H"

    grid._generate_image(outfile=filepath, saveToFile=False)

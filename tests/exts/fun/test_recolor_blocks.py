from pathlib import Path

from bot.exts.fun.mathdoku_parser import create_grids


def test_board_filled_handler(tmp_path: Path) -> None:
    """Contract: The board should be recolored."""
    filepath1 = "testdokuboardfilledcolor1.png"
    filepath2 = "testdokuboardfilledcolor2.png"
    filepath3 = "testdokuboardfilledcolor3.png"

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

    save_to_disk = False
    grid._generate_image(outfile=filepath1, saveToFile=save_to_disk)

    for block in grid.blocks:
        block.color = (255, 255, 255)

    grid._generate_image(outfile=filepath2, saveToFile=save_to_disk)

    grid.recolor_blocks()

    grid._generate_image(outfile=filepath3, saveToFile=save_to_disk)

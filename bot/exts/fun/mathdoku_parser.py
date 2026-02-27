import re
from pathlib import Path

from bot.bot import Bot

from .mathdoku import Block, Grid

FILE_PATH = Path("bot/resources/fun/mathdoku_boards.txt")


async def setup(bot: Bot) -> None:
    """Missing setup function was causing issues."""
    return


def create_grids(file_path: Path = FILE_PATH) -> list[Grid]:
    """
    Creates the board from the result of searching the board file for matches.

    The creation happens in this order:
    1) Create the blocks, set the cells' blocks references to the newly created block (for that cell)
    2) Set the newly created blocks' operations
    3) Read the suggested solution into each cell

    If an error occurs when parsing a board, it is skipped. This function assumes that the appropriate regex has ensured
    safe integer casting.

    Returns a list of succesfully parsed boards.
    """
    matched_grid_strs = _search_for_grids_in_file(file_path)
    grids = {}
    for m_board in matched_grid_strs:
        expected_size = int(m_board[0][0])
        difficulty = m_board[1]
        grid = Grid(expected_size, difficulty=difficulty)
        grid_str = m_board[2]
        operation_str = m_board[3]
        solution_str = m_board[4]
        try:
            created_blocks = _create_cells_and_blocks(expected_size, grid, grid_str)
            _read_block_operations(created_blocks, operation_str)
            _read_solution(grid, solution_str)
        except IndexError:
            continue
        grid.recolor_blocks()
        grids.setdefault(expected_size, {}).setdefault(difficulty, []).append(grid)

    return grids


def _search_for_grids_in_file(file_path: Path = FILE_PATH) -> list[tuple[str, str, str, str]]:
    """
    The function searches the mathdoku file with regex and returns a list of any found boards.

    Regex groups are in the following order:
    1) size & difficulty, e.g. 5x5:d5
    2) board cells & blocks, e.g. EAACC
    3) blocks and their operations, e.g. A 1-
    4) proposed solution, e.g. 1 5 4 3 2.
    """
    matched_boards = re.findall(
        r"""(\d+x\d+:d\d+)\ \((\w+)\)\r?\n
                       ((?:[\d\w]+\r?\n)+)
                       \r?\n
                       ((?:\w\ \d+[\+\-x\/]\r?\n)+)
                       \r?\n
                       ((?:\d+(?:\s+\d+)*\r?\n)+)
                                """,
        file_path.read_text(),
        flags=re.VERBOSE,
    )
    return matched_boards


def _create_cells_and_blocks(expected_size: int, created_grid: Grid, grid_str: str) -> dict[str, Block]:
    """
    The function creates blocks from grid_str, the created grid's cells' blocks are set to reference them.

    Returns a dictionary which maps block ids (i.e. their letter) to their created reference.
    """
    rows = grid_str.split()
    seen_blocks = {}  # seen block "ids"
    if len(rows) != expected_size:
        raise IndexError
    for i, row in enumerate(rows):  # splits on newline
        if len(row) != expected_size:
            raise IndexError
        for j, col in enumerate(row):
            cell = created_grid[i][j]
            if col.isdigit():  # has no block
                block = Block(str(i) + str(j), "", int(col), cell, created_grid)
                cell.block = block
                block.cells.append(cell)
                created_grid.blocks.append(block)
                continue
            if col not in seen_blocks:
                block = Block(col, None, None, cell, created_grid)
                seen_blocks[col] = block
                created_grid.blocks.append(block)
            else:
                block = seen_blocks[col]
            cell.block = block
            cell.color = cell.block.color
            block.cells.append(cell)
    return seen_blocks


def _read_block_operations(created_blocks: dict[str, Block], operation_str: str) -> None:
    """The function reads and sets the block operations of the created blocks."""
    for row in operation_str.splitlines():
        if not row:  # empty
            continue

        row = row.split()
        if len(row) != 2:
            raise IndexError
        id = row[0]
        num, op = int(row[1][:-1]), row[1][-1]
        if id not in created_blocks:  # block hasn't been created
            raise IndexError
        created_blocks[id].number = num
        created_blocks[id].operation = op


def _read_solution(grid: Grid, solution_str: str) -> None:
    """The function reads the solution and sets each cell's proposed correct value."""
    rows = solution_str.splitlines()
    if len(rows) != grid.size:
        raise IndexError
    for i, row in enumerate(rows):
        cols = row.split()
        if len(cols) != grid.size:
            raise IndexError
        for j, col in enumerate(cols):
            grid[i][j].correct = int(col)

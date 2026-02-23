
class Cell:
    """Represents a single cell in the grid."""

    def __init__(self, column: int, row: int) -> None:
        self.column = column
        self.row = row

class Block:
    """Represents a block in the puzzle, with its cells, operation and colour."""

    def __init__(self, cells: list[Cell], label: str, label_cell: Cell, colour: tuple[int, int, int]) -> None:
        self.cells = cells
        self.label = label
        self.label_cell = label_cell
        self.colour = colour

class Grid:
    """Represents the full game board, with all blocks and player guesses."""

    def __init__(self, size: int, blocks: list[Block]) -> None:
        self.size = size
        self.blocks = blocks
        self.guesses: dict[tuple[int, int], int] = {}
        self.cell_block_map: dict[tuple[int, int], Block] = {}

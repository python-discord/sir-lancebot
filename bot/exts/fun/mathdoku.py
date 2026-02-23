

class Cell:
    """Represents a single cell in the grid."""

    def __init__(self, column: int, row: int) -> None:
        self.column = column
        self.row = row
        self.block = None
        self.guess = 0

class Block:
    """Represents a block in the puzzle, with its cells, operation and colour."""

    def __init__(self, operation: str, number: int, label_cell: Cell, colour: tuple[int, int, int]) -> None:
        self.cells = []
        self.operation = operation
        self.number = number
        self.label_cell = label_cell
        self.colour = colour

class Grid:
    """Represents the full game board, with all blocks and player guesses."""

    def __init__(self, size: int) -> None:
        self.size = size
        self.blocks = []
        self.cells = []     # 2D array for cells [row][col]

        self.__create_cells__()

    def __create_cells__(self) -> None: 
        for row in range(self.size):
            self.cells.append([])
            for col in range(self.size):
                self.cells[row].append(Cell(col, row))

    def __str__(self) -> str:
        print_str = "\n"
        for row in range(self.size):
            print_str += "["
            for col in range(self.size - 1):
                print_str += str(self.cells[row][col].guess) + " "
            print_str += str(self.cells[row][col].guess) + "]\n"
        return print_str



        

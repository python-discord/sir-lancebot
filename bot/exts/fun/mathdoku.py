COLORS = [
    (235, 59, 59),
    (199, 61, 50),
    (235, 85, 59),
    (199, 83, 50),
    (235, 111, 59),
    (199, 105, 50),
    (235, 137, 59),
    (199, 127, 50),
    (235, 163, 59),
    (199, 149, 50),
    (235, 189, 59),
    (199, 171, 50),
    (235, 215, 59),
    (199, 193, 50),
    (228, 235, 59),
    (182, 199, 50),
    (202, 235, 59),
    (160, 199, 50),
    (176, 235, 59),
    (138, 199, 50),
    (150, 235, 59),
    (116, 199, 50),
    (124, 235, 59),
    (94, 199, 50),
    (98, 235, 59),
    (72, 199, 50),
    (72, 235, 59),
    (50, 199, 50),
    (59, 235, 72),
    (50, 199, 72),
    (59, 235, 98),
    (50, 199, 94),
    (59, 235, 124),
    (50, 199, 116),
    (59, 235, 150),
    (50, 199, 138),
    (59, 235, 176),
    (50, 199, 160),
    (59, 235, 202),
    (50, 199, 182),
    (59, 235, 228),
    (50, 193, 199),
    (59, 215, 235),
    (50, 171, 199),
    (59, 189, 235),
    (50, 149, 199),
    (59, 163, 235),
    (50, 127, 199),
    (59, 137, 235),
    (50, 105, 199),
    (59, 111, 235),
    (50, 83, 199),
    (59, 85, 235),
    (50, 61, 199),
    (59, 59, 235),
    (61, 50, 199),
    (85, 59, 235),
    (83, 50, 199),
    (111, 59, 235),
    (105, 50, 199),
    (137, 59, 235),
    (127, 50, 199),
    (163, 59, 235),
    (149, 50, 199),
    (189, 59, 235),
    (171, 50, 199),
    (215, 59, 235),
    (193, 50, 199),
    (235, 59, 228),
    (199, 50, 182),
    (235, 59, 202),
    (199, 50, 160),
    (235, 59, 176),
    (199, 50, 138),
    (235, 59, 150),
    (199, 50, 116),
    (235, 59, 124),
    (199, 50, 94),
    (235, 59, 98),
    (199, 50, 72),
    (235, 59, 72),
]


class Cell:
    """Represents a single cell in the grid."""

    def __init__(self, column: int, row: int) -> None:
        self.column = column
        self.row = row
        self.block = None
        self._guess = 0
        self.correct = 0

    @property
    def guess(self):
        return self._guess

    @guess.setter
    def guess(self, new_guess):
        self._guess = new_guess

class Block:
    """Represents a block in the puzzle, with its cells, operation and colour."""

    def __init__(self, id: str, operation: str, number: int, label_cell: Cell) -> None:
        self.id = id
        self.cells = []
        self.operation = operation
        self.number = number
        self.label_cell = label_cell

    @property
    def color(self) -> tuple[int, int, int]:
        """Returns the block's color."""
        c_a = ord(self.id[0]) - ord("A")
        if c_a > 0 and c_a < len(COLORS):
            return COLORS[c_a]

        return COLORS[-1]


class Grid:
    """Represents the full game board, with all blocks and player guesses."""

    def __init__(self, size: int) -> None:
        self.size = size
        self.blocks = []
        self._cells = tuple(
            tuple(Cell(col, row) for col in range(size))
            for row in range(size)
        )   # 2D tupple for cells [row][col]

    @property
    def cells(self):
        return self._cells

    def __str__(self) -> str:
        print_str = "\n"
        for row in range(self.size):
            print_str += "["
            for col in range(self.size - 1):
                print_str += str(self.cells[row][col].guess) + " "
            print_str += str(self.cells[row][col + 1].guess) + "]\n"
        return print_str
    
    def _latin_square_check(self) -> bool:
        """
        Checks if the grid is filled correctly in terms of a latin square.\n
        I.e all numbers in the range per colum and row exist.
        """
        check_structure = [[False for col in range(self.size)] for row in range(self.size)]

        for row in range(self.size):
            for col in range(self.size):
                guess = self.cells[row][col].guess
                if guess == 0:
                    return False
                check_structure[row][guess - 1] = True
            if all(check_structure[row]) is False:
                return False

        return True
    
    def _blocks_fufilled_check(self) -> list[Block] | bool:
        """
        Checks if all the blocks are filled correctly and meets the requirements. \n
        Returns the blocks that are wrong or True if all blocks meet the requirements. \n
        Will return False if the input is invalid. 
        """
        wrong_blocks = []
        for block in self.blocks:
            result = block.cells[0].guess
            if len(block.cells) < 1:
                return False
            if len(block.cells) == 1:
                if block.cells[0].guess != block.number:
                    wrong_blocks.append(block)
                continue
            for cell in block.cells[1:]:
                match block.operation:
                    case "+":
                        result += cell.guess
                    case "-":
                        result -= cell.guess
                    case "x":
                        result *= cell.guess
                    case "/":
                        # Should only be a block of 2 cells for devision
                        result1 = block.cells[0].guess / block.cells[1].guess
                        result2 = block.cells[1].guess / block.cells[0].guess

                        if result1 != block.number and result2 != block.number:
                            wrong_blocks.append(block)
                        else:
                            result = block.number
                        break
            
            if abs(result) != block.number:
                wrong_blocks.append(block)
        
        if len(wrong_blocks) == 0:
            return True
        return wrong_blocks


    def check_victory(self) -> bool:
        """
        Checks if the board is in a state where the player has won and will 
        return True or False
        """
        if self._latin_square_check() and isinstance(self._blocks_fufilled_check(), bool) and self._blocks_fufilled_check():
            return True
        return False
        
                

    def __getitem__(self, i: int) -> list[Cell]:
        """
        Defines the indexing operator for the Grid class.

        Grid[i] will return the i:th row.
        """
        return self.cells[i]

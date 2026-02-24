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

    def __init__(self, id: str, operation: str, number: int, label_cell: Cell, colour: tuple[int, int, int]) -> None:
        self.id = id
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
        
                

    def __getitem__(self, i) -> list[Cell]:
        """
        Defines the indexing operator for the Grid class.

        Grid[i] will return the i:th row.
        """
        return self.cells[i]

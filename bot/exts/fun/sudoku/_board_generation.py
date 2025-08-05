import random
import copy


class GenerateSudokuPuzzle:
    """Generates and solves Sudoku puzzles using a backtracking algorithm."""
    def __init__(self):
        self.counter = 0
        # Path is for the matplotlib animation
        self.path = []
        # Generate the puzzle
        self.grid = [[0 for _ in range(6)] for _ in range(6)]
        self.generate_puzzle()

    def generate_puzzle(self):
        """Generates a new puzzle and solves it."""
        self.generate_solution(self.grid)
        # self.print_grid()
        self.remove_numbers_from_grid()
        self.print_grid()
        return

    def print_grid(self):
        for row in self.grid:
            print(row)
        return

    @staticmethod
    def valid_location(grid, row, col, number):
        """Returns a bool which determines whether the
        number can be placed in the square given by the player."""
        # Checks the row
        if number in grid[row]:
            return False

        # Checks the column
        for i in range(6):
            if grid[i][col] == number:
                return False

        # Checks the subgrid
        start_row = row - row % 2
        start_col = col - col % 3

        for i in range(start_row, (start_row + 2)):
            for j in range(start_col, (start_col + 2)):
                if grid[i][j] == number: 
                    return False

        else:
            return True

    @staticmethod
    def find_empty_square(grid):
        """Return the next empty square coordinates in the grid."""
        for i in range(6):
            for j in range(6):
                if grid[i][j] == 0:
                    return [i, j]
        return

    @staticmethod
    def yield_coords():
        for i in range(0, 36):
            yield i // 6, i % 6

    def generate_solution(self, grid):
        number_list = [1, 2, 3, 4, 5, 6]

        empty = self.find_empty_square(grid)
        if not empty:
            return True  # board is complete

        row, col = empty
        random.shuffle(number_list)

        for number in number_list:
            if self.valid_location(grid, row, col, number):
                grid[row][col] = number
                self.path.append((number, row, col))

                if self.generate_solution(grid):
                    return True

                grid[row][col] = 0

        return False

    @staticmethod
    def get_non_empty_squares(grid):
        """Returns a shuffled list of non-empty squares in the puzzle."""
        non_empty_squares = []
        for i in range(len(grid)):
            for j in range(len(grid)):
                if grid[i][j] != 0:
                    non_empty_squares.append((i, j))
        random.shuffle(non_empty_squares)
        return non_empty_squares

    def remove_numbers_from_grid(self):
        """Remove numbers from the grid to create the puzzle."""
        # Get all non-empty squares from the grid
        non_empty_squares = self.get_non_empty_squares(self.grid)
        non_empty_squares_count = len(non_empty_squares)
        rounds = 3
        while rounds > 0 and len(self.get_non_empty_squares(self.grid)) >= 11:
            # There should be at least 11 clues for easy puzzles,
            # 10 clues for medium puzzles, and 9 clues for hard puzzles.
            row, col = non_empty_squares.pop()
            non_empty_squares_count -= 1
            # Might need to put the square value back if there is more than one solution
            # removed_square = self.grid[row][col]
            self.grid[row][col] = 0
            # Make a copy of the grid to solve
            # grid_copy = copy.deepcopy(self.grid)
            # Initialize solutions counter to zero
            self.counter = 0
            # self.solve_puzzle(grid_copy)
        return

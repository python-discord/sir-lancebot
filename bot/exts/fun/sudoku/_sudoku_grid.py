import copy
import random
from collections import Counter
from typing import Literal

from PIL import Image, ImageDraw, ImageFont

type SudokuDifficulty = Literal["easy", "normal", "hard"]

GIVEN_DIGITS: dict[SudokuDifficulty, int] = {
    "easy": 13,
    "normal": 11,
    "hard": 9,
}

BLACK = (0, 0, 0)
SUDOKU_TEMPLATE_PATH = "bot/resources/fun/sudoku_template.png"
NUMBER_FONT = ImageFont.truetype("bot/resources/fun/Roboto-Medium.ttf", 99)


class SudokuGrid:
    """Generates and solves Sudoku puzzles."""

    def __init__(self, difficulty: SudokuDifficulty = "normal"):
        self.difficulty: SudokuDifficulty = difficulty
        self.given_digits = GIVEN_DIGITS[difficulty]

        # Correct solution to the puzzle
        self.solution: list[list[int]] = self.generate_solution()

        # Digits shown to the user
        self.puzzle: list[list[int]] = copy.deepcopy(self.solution)

        # Track of empty squares used to speed up processing
        self.empty_squares: set[tuple[int, int]] = set()
        puzzle_digits: Counter[int] = Counter({i: 6 for i in range(1, 7)})

        # Attempt to remove digits in a random order
        positions = [(r, c) for r in range(6) for c in range(6)]
        random.shuffle(positions)
        for r, c in positions:
            digit = self.solution[r][c]

            # Cannot remove 2 digits entirely since it breaks uniqueness
            if 0 in puzzle_digits.values() and puzzle_digits[digit] == 1:
                continue

            # Remove the digit
            self.puzzle[r][c] = 0
            self.empty_squares.add((r, c))
            puzzle_digits -= {digit: 1}

            # If the solution is no longer unique, revert
            if not self.has_unique_solution():
                self.puzzle[r][c] = digit
                self.empty_squares.remove((r, c))
                puzzle_digits += {digit: 1}

            # Stop when all the given digits have been set based on the difficulty
            if puzzle_digits.total() <= self.given_digits:
                break

        # Initialize image
        self.image: Image.Image = Image.open(SUDOKU_TEMPLATE_PATH)
        for x, row in enumerate(self.puzzle):
            for y, digit in enumerate(row):
                if digit == 0:
                    continue
                self.draw_digit((x, y), digit)

    @staticmethod
    def generate_solution() -> list[list[int]]:
        """Generate a random complete 6x6 sudoku grid."""
        # Offset added to each row/column, arranged into subgrids
        row_boxes = [[0, 1, 2], [3, 4, 5]]
        col_boxes = [[0, 3], [1, 4], [2, 5]]

        # Row permutation
        for box in row_boxes:
            random.shuffle(box)
        random.shuffle(row_boxes)

        # Column permutation
        for box in col_boxes:
            random.shuffle(box)
        random.shuffle(col_boxes)

        rows = row_boxes[0] + row_boxes[1]
        cols = col_boxes[0] + col_boxes[1] + col_boxes[2]

        number_mapping = list(range(1, 7))
        random.shuffle(number_mapping)

        # Create the grid
        grid = [
            [number_mapping[(row + col) % 6] for col in cols]
            for row in rows
        ]

        return grid

    def draw_digit(self, position: tuple[int, int], digit: int, fill: tuple[int, int, int] = BLACK) -> None:
        """Draws a digit in the given position on the Sudoku board."""
        pos_x = int(position[1]) * 83 + 95
        pos_y = int(position[0]) * 83 + 6
        ImageDraw.Draw(self.image).text(
            (pos_x, pos_y),
            str(digit),
            fill=fill,
            font=NUMBER_FONT,
            align="center",
        )

    def has_unique_solution(self) -> bool:
        """Brute force search the empty squares to see if an alternate solution exists."""
        # Base case (grid complete)
        if not self.empty_squares:
            # Return False (i.e. non-unique) if a different solution is found
            return self.puzzle == self.solution

        r, c = self.empty_squares.pop()
        possible_digits = set(range(1, 7))

        # Check row
        possible_digits -= set(self.puzzle[r])

        # Check column
        possible_digits -= set(self.puzzle[i][c] for i in range(6))

        # Check subgrid
        sub_r = r - r % 2
        sub_c = c - c % 3
        for i in range(sub_r, sub_r + 2):
            for j in range(sub_c, sub_c + 3):
                possible_digits.discard(self.puzzle[i][j])

        # DFS the rest of the solution
        is_unique = True
        for digit in possible_digits:
            self.puzzle[r][c] = digit
            if not self.has_unique_solution():
                is_unique = False
                break
        self.puzzle[r][c] = 0
        self.empty_squares.add((r, c))

        return is_unique

    def is_empty(self, position: tuple[int, int]) -> bool:
        """Checks if a given square is empty."""
        return position in self.empty_squares

    def is_solved(self) -> bool:
        """Returns whether the sudoku puzzle is complete."""
        return self.puzzle == self.solution

    def guess(self, position: tuple[int, int], digit: int) -> bool:
        """Guess the digit of a given square, and update the board if correct."""
        if not self.is_empty(position):
            return False

        row, col = position
        if self.solution[row][col] == digit:
            self.puzzle[row][col] = digit
            self.empty_squares.remove(position)
            self.draw_digit(position, digit)
            return True
        return False

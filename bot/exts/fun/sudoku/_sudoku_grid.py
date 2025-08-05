from collections import Counter
import random
import copy


NUM_GIVEN_DIGITS = 12


class SudokuGrid:
    def __init__(self):
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

            # Stop when there are 12 given digits
            if puzzle_digits.total() <= NUM_GIVEN_DIGITS:
                break

    @staticmethod
    def generate_solution():
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

    def has_unique_solution(self) -> bool:
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

from datetime import datetime
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from random import randint

COLORS = [
    (255, 50, 50),
    (255, 66, 50),
    (255, 81, 50),
    (255, 96, 50),
    (255, 111, 50),
    (255, 126, 50),
    (255, 141, 50),
    (255, 156, 50),
    (255, 171, 50),
    (255, 187, 50),
    (255, 202, 50),
    (255, 217, 50),
    (255, 232, 50),
    (255, 247, 50),
    (247, 255, 50),
    (232, 255, 50),
    (217, 255, 50),
    (202, 255, 50),
    (187, 255, 50),
    (171, 255, 50),
    (156, 255, 50),
    (141, 255, 50),
    (126, 255, 50),
    (111, 255, 50),
    (96, 255, 50),
    (81, 255, 50),
    (66, 255, 50),
    (50, 255, 50),
    (50, 255, 66),
    (50, 255, 81),
    (50, 255, 96),
    (50, 255, 111),
    (50, 255, 126),
    (50, 255, 141),
    (50, 255, 156),
    (50, 255, 171),
    (50, 255, 186),
    (50, 255, 202),
    (50, 255, 217),
    (50, 255, 232),
    (50, 255, 247),
    (50, 247, 255),
    (50, 232, 255),
    (50, 217, 255),
    (50, 202, 255),
    (50, 186, 255),
    (50, 171, 255),
    (50, 156, 255),
    (50, 141, 255),
    (50, 126, 255),
    (50, 111, 255),
    (50, 96, 255),
    (50, 81, 255),
    (50, 66, 255),
    (50, 50, 255),
    (66, 50, 255),
    (81, 50, 255),
    (96, 50, 255),
    (111, 50, 255),
    (126, 50, 255),
    (141, 50, 255),
    (156, 50, 255),
    (171, 50, 255),
    (187, 50, 255),
    (202, 50, 255),
    (217, 50, 255),
    (232, 50, 255),
    (247, 50, 255),
    (255, 50, 247),
    (255, 50, 232),
    (255, 50, 217),
    (255, 50, 202),
    (255, 50, 187),
    (255, 50, 171),
    (255, 50, 156),
    (255, 50, 141),
    (255, 50, 126),
    (255, 50, 111),
    (255, 50, 96),
    (255, 50, 81),
    (255, 50, 66),
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
    def guess(self, new_guess) -> None:
        self._guess = new_guess


class Block:
    """Represents a block in the puzzle, with its cells, operation and colour."""

    color_id = 0
    color_offset = randint(0, 80)

    def __init__(self, id: str, operation: str, number: int, label_cell: Cell) -> None:
        self.id = id
        self.cells = []
        self.operation = operation
        self.number = number
        self.label_cell = label_cell
        self.color_id = Block.color_id
        self.color = self.compute_color()

        Block.color_id += 1

    def compute_color(self) -> tuple[int, int, int]:
        """Computes the block's color."""
        c_a = ord(self.id[0]) ** 2 - ord("A")
        return COLORS[c_a % len(COLORS)]


class Grid:
    """Represents the full game board, with all blocks and player guesses."""

    HINT_COOLDOWN_SECONDS = 180  # 3 minutes of hint cooldown.

    def __init__(self, size: int, difficulty: str | None = None) -> None:
        self.size = size
        self.blocks = []
        self._cells = tuple(
            tuple(Cell(col, row) for col in range(size)) for row in range(size)
        )  # 2D tupple for cells [row][col]

        self._last_hint_timestamp = None
        self.difficulty = difficulty

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
        return True or False.
        """
        return bool(
            self._latin_square_check()
            and isinstance(self._blocks_fufilled_check(), bool)
            and self._blocks_fufilled_check()
        )

    def board_filled_handler(self) -> bool:
        """
        Handler for when board is filled.\n
        The method calls the victory check and colors in the blocks that are not fufilled if any,\n
        and returns True or False if the board is solved.
        """
        wrong_blocks = self._blocks_fufilled_check()
        if isinstance(wrong_blocks, bool):
            wrong_blocks = []

        for block in self.blocks:
            if block in wrong_blocks:
                block.color = (255, 0, 0)
            else:
                block.color = (100, 255, 100)

        return self.check_victory()

    def check_full_grid(self) -> bool:
        """Helper that checks if a grid is completely filled."""
        for i in range(self.size):
            for cell in self.cells[i]:
                if cell.guess <= 0:
                    return False
        return True

    def recolor_blocks(self) -> None:
        """Method to recolor all blocks in their original color."""
        for block in self.blocks:
            block.color = block.compute_color()

    def __getitem__(self, i: int) -> list[Cell]:
        """
        Defines the indexing operator for the Grid class.

        Grid[i] will return the i:th row.
        """
        return self.cells[i]

    def _generate_image(self, cellSize=80, margin=30, outfile="mathdoku.png", saveToFile=False) -> None:
        """Print the Grid to."""
        fontLable = ImageFont.load_default(15)
        fontGuess = ImageFont.load_default(30)
        img = Image.new(
            "RGB", (cellSize * len(self.cells) + 2 * margin, cellSize * len(self.cells) + 2 * margin), "white"
        )
        draw = ImageDraw.Draw(img)

        for i, row in enumerate(self.cells):
            for j, cell in enumerate(row):
                # 1) The block color
                x_start = (cell.column) * cellSize + margin + margin // 2
                y_start = (cell.row) * cellSize + margin + margin // 2
                x_end = (cell.column) * cellSize + cellSize + margin + margin // 2
                y_end = (cell.row) * cellSize + cellSize + margin + margin // 2
                color = cell.block.color
                draw.rectangle((x_start, y_start, x_end, y_end), fill=color)

                # 2) the guess
                guess = cell.guess
                if guess != 0:
                    draw.text((x_start + 30, y_start + 22), str(guess), fill="black", font=fontGuess)

                # 3) the lines between the cells
                thin_line_width = 2
                draw.line((x_start, y_start, x_start + cellSize, y_start), fill="black", width=thin_line_width)
                draw.line((x_end, y_start, x_end, y_end), fill="black", width=thin_line_width)
                draw.line((x_start, y_start, x_start, y_start + cellSize), fill="black", width=thin_line_width)
                draw.line((x_start, y_end, x_end, y_end), fill="black", width=thin_line_width)

                n_over = 1
                n_under = 1
                n_right = 1
                n_left = 1

                if i == 0:
                    n_over = 0
                if i == len(self.cells) - 1:
                    n_under = 0
                if j == 0:
                    n_left = 0
                if j == len(row) - 1:
                    n_right = 0

                thick_line_width = 5
                offset = 2

                if self.cells[i - n_over][j].block.id != cell.block.id or self.cells[i - n_over][j] is cell:
                    draw.line(
                        (x_start - offset, y_start, x_end + offset, y_start), fill="black", width=thick_line_width
                    )
                if self.cells[i + n_under][j].block.id != cell.block.id or self.cells[i + n_under][j] is cell:
                    draw.line((x_start - offset, y_end, x_end + offset, y_end), fill="black", width=thick_line_width)
                if self.cells[i][j - n_left].block.id != cell.block.id or self.cells[i][j - n_left] is cell:
                    draw.line((x_start, y_start, x_start, y_end), fill="black", width=thick_line_width)
                if self.cells[i][j + n_right].block.id != cell.block.id or self.cells[i][j + n_right] is cell:
                    draw.line((x_end, y_start, x_end, y_end), fill="black", width=thick_line_width)

        for block in self.blocks:
            # 4) the lable of the block - in the top left corner of the lable cell
            label_cell = block.label_cell
            label = str(block.number) + " " + str(block.operation)
            x_start = (label_cell.column) * cellSize + margin + margin // 2
            y_start = (label_cell.row) * cellSize + margin + margin // 2
            # print("Label:" + label )
            draw.text((x_start + 4, y_start + 2), str(label), fill="black", font=fontLable)

        # 5) the x axis description A-...
        for i in range(self.size):
            text = chr(ord("A") + i)
            draw.text((margin + 30 + i * cellSize + margin // 2, 4), str(text), fill="black", font=fontGuess)

        # 6) the y axis description 1-...
        for j in range(self.size):
            text = str(j + 1)
            draw.text((13, margin + 22 + j * cellSize + margin // 2), str(text), fill="black", font=fontGuess)

        if saveToFile:
            img.save(outfile)

        buffer = BytesIO()
        img.save(buffer, "PNG")
        buffer.seek(0)
        return buffer

    def _find_first_empty_cell(self):
        """Return the first empty cell (`guess == 0`) in row-major order, or `None` if all cells are filled."""
        for row in self.cells:
            for cell in row:
                if cell.guess == 0:
                    return cell, "empty"

        return None

    def hint(self, now: datetime | None = None):
        """Return a hint for the first empty cell, or cooldown/all-filled info if a hint cannot be given."""
        current_time = datetime.now() if now is None else now

        if self._last_hint_timestamp is not None:
            elapsed = (current_time - self._last_hint_timestamp).total_seconds()
            if elapsed < self.HINT_COOLDOWN_SECONDS:
                return {
                    "type": "cooldown",
                    "remaining_seconds": int(self.HINT_COOLDOWN_SECONDS - elapsed),
                }

        found = self._find_first_empty_cell()
        if found is None:
            return {"type": "all filled cells"}

        cell, _reason = found

        self._last_hint_timestamp = current_time

        coord = f"{chr(ord('A') + cell.column)}{cell.row + 1}"
        return {
            "type": "hint",
            "guess": f"{coord} {cell.correct}",
        }

    def add_guess(self, guess) -> bool:
        """
        Takes the user guess and checks if its valid, if it is -> add to cell
        A guess is in format A5 4, where A = column, 5 = row and 4 = guessed value.
        """
        guess = guess.split()
        column = ord(guess[0][0].lower()) - 97
        row = int(guess[0][1]) - 1
        value = int(guess[1])

        if column < 0 or row < 0 or value < 1:
            return False

        if column >= self.size or row >= self.size or value > self.size:
            return False

        self.cells[row][column].guess = value
        return True

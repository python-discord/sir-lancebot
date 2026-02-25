import os

from bot.exts.fun.mathdoku import Grid, Block

def test_image_generation():
    # Contract: The generate image function should when called generate an image file named
    # "mathdoku.png"

    filepath = "testdoku.png"
    if (os.path.exists(filepath)): 
        os.remove(filepath)
    assert os.path.exists(filepath) is False

    # setup testGrid
    testingGrid = Grid(3)
    cell_one = testingGrid.cells[0][0]
    cell_two = testingGrid.cells[0][1]
    cell_three = testingGrid.cells[0][2]
    cell_four = testingGrid.cells[1][0]
    cell_five = testingGrid.cells[1][1]
    cell_six = testingGrid.cells[1][2]
    cell_seven = testingGrid.cells[2][0]
    cell_eight = testingGrid.cells[2][1]
    cell_nine = testingGrid.cells[2][2]
    testBlock_1 = Block("A", "+", 3, cell_one)
    testBlock_2 = Block("B", "/", 30, cell_four)
    testBlock_3 = Block("C", "-", 300, cell_five)
    testingGrid.blocks.append(testBlock_1)
    testingGrid.blocks.append(testBlock_2)
    testingGrid.blocks.append(testBlock_3)

    cell_one.guess = 1
    cell_three.guess = 3  
    cell_seven.guess = 4

    testBlock_1.cells.append(cell_one)
    testBlock_1.cells.append(cell_two)
    testBlock_1.cells.append(cell_three)
    cell_one.block = testBlock_1
    cell_two.block = testBlock_1
    cell_three.block = testBlock_1

    testBlock_2.cells.append(cell_four)
    testBlock_2.cells.append(cell_seven)
    testBlock_2.cells.append(cell_eight)
    testBlock_2.cells.append(cell_nine)
    cell_four.block = testBlock_2
    cell_seven.block = testBlock_2
    cell_eight.block = testBlock_2
    cell_nine.block = testBlock_2

    testBlock_3.cells.append(cell_five)
    testBlock_3.cells.append(cell_six)
    cell_five.block = testBlock_3
    cell_six.block = testBlock_3

    testingGrid._generate_image(outfile=filepath, saveToFile=True)
    assert os.path.exists(filepath)
    if (os.path.exists(filepath)): 
        os.remove(filepath)

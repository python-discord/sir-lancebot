from bot.exts.fun.mathdoku import Grid, Block, Cell


def test_grid():
    """
    Contract: No errors should be thrown when setting up the grid and the initial
    guess of a cell should be 0.
    """
    grid = Grid(5)
    assert grid.cells[0][0].guess == 0 
    print(grid)

def test_latin_square_check():
    """
    Contract: _latin_square_check() should only return true if
    the grid is a latin square
    """
    grid = Grid(5)
    
    #Makes a latin square 
    for row in range(grid.size):
        for col in range(grid.size):
            grid.cells[row][col].guess = ((row + col) % grid.size) + 1
    
    print(grid)
    
    assert grid._latin_square_check() 
    
    grid.cells[3][3].guess = 1

    assert grid._latin_square_check() is False

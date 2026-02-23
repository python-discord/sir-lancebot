from bot.exts.fun.mathdoku import Grid, Block, Cell


def test_grid():
    grid = Grid(5)
    assert grid.cells[0][0].guess == 0 
    print(grid)
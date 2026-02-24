from bot.exts.fun.mathdoku import Block


def test_block_with_id_gets_color() -> None:
    """Tests that a block with an id of A gets a color."""
    block = Block("A", None, None, None)
    assert type(block.color) is tuple
    assert len(block.color) == 3


def test_block_with_unexpected_id_gets_color() -> None:
    """Tests that a block with an unexpected id still gets a color."""
    block = Block("9ZZZ", None, None, None)
    assert type(block.color) is tuple
    assert len(block.color) == 3

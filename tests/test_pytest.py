"""
How to run pytest:
1. Check python --version and see that it is 3.13.X
2. run pip install pytest
3. run pip install pytest-asyncio
4. run this to actually run the tests: python -m pytest tests/
"""


def test_pytest():
    """A simple sanity check to ensure pytest is working."""
    assert 3 == 3
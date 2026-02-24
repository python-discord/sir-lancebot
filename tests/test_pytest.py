"""
How to run pytest:
For venv:
1. python venv venv
2. add venv or uv or install all dependecies uising:
pip install pydis-core[all]==11.8.0 arrow==1.3.0 
beautifulsoup4==4.12.3 colorama==0.4.6 coloredlogs==15.0.1 
emoji==2.14.0 emojis==0.7.0 lxml==6.0.0 pillow==12.1.1 pydantic==2.10.1 
pydantic-settings==2.8.1 pyjokes==0.8.3 PyYAML==6.0.2 rapidfuzz==3.12.2 sentry-sdk==2.19.2

3. run pip install pytest
4. run this to actually run the tests: python -m pytest -s
"""


def test_pytest():
    """A simple sanity check to ensure pytest is working."""
    assert 3 == 3
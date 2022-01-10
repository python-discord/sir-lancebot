import sys
from pathlib import Path
from typing import BinaryIO

import matplotlib.pyplot as plt

# configure fonts and colors for matplotlib
plt.rcParams.update(
    {
        "font.size": 16,
        "mathtext.fontset": "cm",  # Computer Modern font set
        "mathtext.rm": "serif",
        "figure.facecolor": "36393F",  # matches Discord's dark mode background color
        "text.color": "white",
    }
)


def render(text: str, file_handle: BinaryIO) -> None:
    """
    Saves rendered image in `file_handle`.

    In case the input is invalid latex, it prints the error to `stderr`.
    """
    fig = plt.figure()
    fig.text(0, 1, text, horizontalalignment="left", verticalalignment="top")
    try:
        plt.savefig(file_handle, bbox_inches="tight", dpi=600)
    except ValueError as err:
        # get rid of traceback, keeping just the latex error
        sys.exit(err)


def main() -> None:
    """
    Renders a latex query and saves the output in a specified file.

    Expects two command line arguments: the query and the path to the output file.
    """
    query = sys.argv[1]
    out_file_path = Path(sys.argv[2])
    with open(out_file_path, "wb") as out_file:
        render(query, out_file)


if __name__ == "__main__":
    main()

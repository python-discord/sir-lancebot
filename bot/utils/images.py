from io import BytesIO
from typing import BinaryIO

from PIL import Image


def process_image(data: bytes, out_file: BinaryIO, pad: int) -> None:
    """Read `data` as an image file, and paste it on a white background."""
    image = Image.open(BytesIO(data)).convert("RGBA")
    width, height = image.size
    background = Image.new("RGBA", (width + 2 * pad, height + 2 * pad), "WHITE")

    # paste the image on the background, using the same image as the mask
    # when an RGBA image is passed as the mask, its alpha band is used.
    # this has the effect of skipping pasting the pixels where the image is transparent.
    background.paste(image, (pad, pad), image)
    background.save(out_file)

from io import BytesIO
from typing import BinaryIO

from PIL import Image, ImageChops


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


def crop_background(
    img: Image.Image, background_color: tuple[int, ...], pad: int = 0
) -> Image.Image | None:
    """
    Crops the image to include only the pixels that aren't the `background_color`. Optionally leaves some padding.

    If the image is totally empty, returns None if pad==0, otherwise an empty image of only the padding.
    """
    if not pad >= 0:
        raise ValueError(f"pad must be >=0, got {pad}")

    # https://stackoverflow.com/a/48605963
    bg = Image.new(img.mode, img.size, background_color)
    diff = ImageChops.difference(img, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if not bbox:
        if pad == 0:
            return None
        # empty image with padding-related sizes
        bbox = (0, 0, 2 * pad, 2 * pad)
    else:
        l, u, r, b = bbox  # noqa: E741
        bbox = (
            max(l - pad, 0),
            max(u - pad, 0),
            min(r + pad, img.width),
            min(b + pad, img.height),
        )
    return img.crop(bbox)

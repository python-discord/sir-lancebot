from PIL import ImageOps


def inversion(im):
    """Inverts an image.

    Returns an inverted image when supplied with an Image object.
    """
    im = im.convert('RGB')
    inv = ImageOps.invert(im)
    return inv

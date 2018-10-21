from PIL import ImageOps


def inversion(im):
    im = im.convert('RGB')
    inv = ImageOps.invert(im)
    return inv

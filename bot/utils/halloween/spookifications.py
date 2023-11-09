import logging
from random import choice, randint

from PIL import Image, ImageOps

log = logging.getLogger()


def inversion(im: Image.Image) -> Image.Image:
    """
    Inverts the image.

    Returns an inverted image when supplied with an Image object.
    """
    im = im.convert("RGB")
    inv = ImageOps.invert(im)
    return inv


def pentagram(im: Image.Image) -> Image.Image:
    """Adds pentagram to the image."""
    im = im.convert("RGB")
    wt, ht = im.size
    penta = Image.open("bot/resources/holidays/halloween/bloody-pentagram.png")
    penta = penta.resize((wt, ht))
    im.paste(penta, (0, 0), penta)
    return im


def bat(im: Image.Image) -> Image.Image:
    """
    Adds a bat silhouette to the image.

    The bat silhouette is of a size at least one-fifths that of the original image and may be rotated
    up to 90 degrees anti-clockwise.
    """
    im = im.convert("RGB")
    wt, _ = im.size
    bat = Image.open("bot/resources/holidays/halloween/bat-clipart.png")
    bat_size = randint(wt//10, wt//7)
    rot = randint(0, 90)
    bat = bat.resize((bat_size, bat_size))
    bat = bat.rotate(rot)
    x = randint(wt-(bat_size * 3), wt-bat_size)
    y = randint(10, bat_size)
    im.paste(bat, (x, y), bat)
    im.paste(bat, (x + bat_size, y + (bat_size // 4)), bat)
    im.paste(bat, (x - bat_size, y - (bat_size // 2)), bat)
    return im


def get_random_effect(im: Image.Image) -> Image.Image:
    """Randomly selects and applies an effect."""
    effects = [inversion, pentagram, bat]
    effect = choice(effects)
    log.info("Spookyavatar's chosen effect: " + effect.__name__)
    return effect(im)

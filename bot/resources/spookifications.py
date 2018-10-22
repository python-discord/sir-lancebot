import logging
from random import choice, randint

from PIL import Image
from PIL import ImageOps

log = logging.getLogger()


def inversion(im):
    """Inverts an image.

    Returns an inverted image when supplied with an Image object.
    """
    im = im.convert('RGB')
    inv = ImageOps.invert(im)
    return inv


def pentagram(im):
    """Adds pentagram to image."""
    im = im.convert('RGB')
    wt, ht = im.size
    penta = Image.open('bot/resources/bloody-pentagram.png')
    penta = penta.resize((wt, ht))
    im.paste(penta, (0, 0), penta)
    return im


def bat(im):
    """Adds a bat silhoutte to the image.

    The bat silhoutte is of a size at least one-fifths that of the original
    image and may be rotated upto 90 degrees anti-clockwise."""
    im = im.convert('RGB')
    wt, ht = im.size
    bat = Image.open('bot/resources/bat-clipart.png')
    bat_size = randint(wt//5, wt)
    rot = randint(0, 90)
    bat = bat.resize((bat_size, bat_size))
    bat = bat.rotate(rot)
    x = randint(0, wt-bat_size)
    y = randint(0, wt-bat_size)
    im.paste(bat, (x, y), bat)
    return im


def get_random_effect(im):
    """Randomly selects and applies an effect."""
    effects = [inversion, pentagram, bat]
    effect = choice(effects)
    log.info("Spookyavatar's chosen effect:" + str(effect))
    return effect(im)

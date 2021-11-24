import logging
from random import choice, randint

from PIL import Image

log = logging.getLogger()


def hat(im: Image) -> Image:
    """Adds a Christmas hat to the image."""
    im = im.convert("RGB")
    wt, ht = im.size
    hat = Image.open("bot/resources/holidays/christmas/christmas-hat.png")
    hat_size = randint(wt // 10, wt // 7)
    rot = randint(0, 90)
    hat = hat.resize((hat_size, hat_size))
    hat = hat.rotate(rot)
    x = randint(wt - (hat_size * 3), wt - hat_size)
    y = randint(10, hat_size)
    im.paste(hat, (x, y), hat)
    im.paste(hat, (x + hat_size, y + (hat_size // 4)), hat)
    im.paste(hat, (x - hat_size, y - (hat_size // 2)), hat)
    return im


def snowflake(im: Image) -> Image:
    """
    Adds a snowflake to the image.

    The snowflake is of a size at least one-fifths that of the original image and may be rotated
    up to 90 degrees anti-clockwise.
    """
    im = im.convert("RGBA")
    wt, ht = im.size
    snowflake = Image.open("bot/resources/holidays/christmas/snowflake.png").convert("RGBA")
    snowflake_size = randint(wt // 10, wt // 7)
    rot = randint(0, 90)
    snowflake = snowflake.resize((snowflake_size, snowflake_size))
    snowflake = snowflake.rotate(rot)
    x = randint(wt-(snowflake_size * 3), wt-snowflake_size)
    y = randint(10, snowflake_size)
    im.paste(snowflake, (x, y), snowflake)
    im.paste(snowflake, (x + snowflake_size, y + (snowflake_size // 4)), snowflake)
    im.paste(snowflake, (x - snowflake_size, y - (snowflake_size // 2)), snowflake)
    return im


def present(im: Image) -> Image:
    """
    Adds a present to the image.

    The present is of a size at least one-fifths that of the original image and may be rotated
    up to 90 degrees anti-clockwise.
    """
    im = im.convert("RGB")
    wt, ht = im.size
    present = Image.open("bot/resources/holidays/christmas/present.png")
    present_size = randint(wt//10, wt//7)
    rot = randint(0, 90)
    present = present.resize((present_size, present_size))
    present = present.rotate(rot)
    x = randint(wt-(present_size * 3), wt-present_size)
    y = randint(10, present_size)
    im.paste(present, (x, y), present)
    im.paste(present, (x + present_size, y + (present_size // 4)), present)
    im.paste(present, (x - present_size, y - (present_size // 2)), present)
    return im


def get_random_effect(im: Image) -> Image:
    """Randomly selects and applies an effect."""
    effects = [hat, snowflake, present]
    effect = choice(effects)
    log.info("Christmasavatar's chosen effect: " + effect.__name__)
    return effect(im)

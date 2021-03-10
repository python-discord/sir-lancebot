import typing as t
from io import BytesIO
from pathlib import Path

import discord
from PIL import Image, ImageDraw, ImageOps

from bot.constants import Colours


class PfpEffects:
    """
    Implements various image effects.

    All of these methods are blocking, so should be ran in threads.
    """

    @staticmethod
    def apply_effect(image_bytes: bytes, effect: t.Callable, *args) -> discord.File:
        """Applies the given effect to the image passed to it."""
        im = Image.open(BytesIO(image_bytes))
        im = im.convert("RGBA")
        im = effect(im, *args)

        bufferedio = BytesIO()
        im.save(bufferedio, format="PNG")
        bufferedio.seek(0)

        return discord.File(bufferedio, filename="modified_avatar.png")

    @staticmethod
    def closest(x: t.Tuple[int, int, int]) -> t.Tuple[int, int, int]:
        """
        Finds the closest easter colour to a given pixel.

        Returns a merge between the original colour and the closest colour.
        """
        r1, g1, b1 = x

        def distance(point: t.Tuple[int, int, int]) -> t.Tuple[int, int, int]:
            """Finds the difference between a pastel colour and the original pixel colour."""
            r2, g2, b2 = point
            return (r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2

        closest_colours = sorted(Colours.easter_like_colours, key=lambda point: distance(point))
        r2, g2, b2 = closest_colours[0]
        r = (r1 + r2) // 2
        g = (g1 + g2) // 2
        b = (b1 + b2) // 2

        return r, g, b

    @staticmethod
    def crop_avatar_circle(avatar: Image) -> Image:
        """This crops the avatar given into a circle."""
        mask = Image.new("L", avatar.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + avatar.size, fill=255)
        avatar.putalpha(mask)
        return avatar

    @staticmethod
    def crop_ring(ring: Image, px: int) -> Image:
        """This crops the given ring into a circle."""
        mask = Image.new("L", ring.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + ring.size, fill=255)
        draw.ellipse((px, px, 1024-px, 1024-px), fill=0)
        ring.putalpha(mask)
        return ring

    @staticmethod
    def pridify_effect(
        image: Image,
        pixels: int,
        flag: str
    ) -> Image:
        """Applies the pride effect to the given image."""
        image = image.resize((1024, 1024))
        image = PfpEffects.crop_avatar_circle(image)

        ring = Image.open(Path(f"bot/resources/pride/flags/{flag}.png")).resize((1024, 1024))
        ring = ring.convert("RGBA")
        ring = PfpEffects.crop_ring(ring, pixels)

        image.alpha_composite(ring, (0, 0))
        return image

    @staticmethod
    def eight_bitify_effect(image: Image) -> Image:
        """
        Applies the 8bit effect to the given image.

        This is done by reducing the image to 32x32 and then back up to 1024x1024.
        We then quantize the image before returning too.
        """
        image = image.resize((32, 32), resample=Image.NEAREST)
        image = image.resize((1024, 1024), resample=Image.NEAREST)
        return image.quantize()

    @staticmethod
    def easterify_effect(image: Image, overlay_image: Image = None) -> Image:
        """Applies the easter effect to the given image."""
        if overlay_image:
            ratio = 64 / overlay_image.height
            overlay_image = overlay_image.resize((
                round(overlay_image.width * ratio),
                round(overlay_image.height * ratio)
            ))
            overlay_image = overlay_image.convert("RGBA")
        else:
            overlay_image = overlay_image = Image.open(Path("bot/resources/easter/chocolate_bunny.png"))

        alpha = image.getchannel("A").getdata()
        image = image.convert("RGB")
        image = ImageOps.posterize(image, 6)

        data = image.getdata()
        data_set = set(data)
        easterified_data_set = {}

        for x in data_set:
            easterified_data_set[x] = PfpEffects.closest(x)
        new_pixel_data = [
            (*easterified_data_set[x], alpha[i])
            if x in easterified_data_set else x
            for i, x in enumerate(data)
        ]

        im = Image.new("RGBA", image.size)
        im.putdata(new_pixel_data)
        im.alpha_composite(
            overlay_image,
            (im.width - overlay_image.width, (im.height - overlay_image.height) // 2)
        )
        return im

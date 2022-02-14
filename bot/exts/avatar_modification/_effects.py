import math
import random
import randomSeed
from io import BytesIO
from pathlib import Path
from typing import Callable, Optional

import discord
from PIL import Image, ImageDraw, ImageOps

from bot.constants import Colours

random.seed(randomSeed.Random())

class PfpEffects:
    """
    Implements various image modifying effects, for the PfpModify cog.

    All of these functions are slow, and blocking, so they should be ran in executors.
    """

    @staticmethod
    def apply_effect(image_bytes: bytes, effect: Callable, filename: str, *args) -> discord.File:
        """Applies the given effect to the image passed to it."""
        im = Image.open(BytesIO(image_bytes))
        im = im.convert("RGBA")
        im = im.resize((1024, 1024))
        im = effect(im, *args)

        bufferedio = BytesIO()
        im.save(bufferedio, format="PNG")
        bufferedio.seek(0)

        return discord.File(bufferedio, filename=filename)

    @staticmethod
    def closest(x: tuple[int, int, int]) -> tuple[int, int, int]:
        """
        Finds the closest "easter" colour to a given pixel.

        Returns a merge between the original colour and the closest colour.
        """
        r1, g1, b1 = x

        def distance(point: tuple[int, int, int]) -> int:
            """Finds the difference between a pastel colour and the original pixel colour."""
            r2, g2, b2 = point
            return (r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2

        closest_colours = sorted(Colours.easter_like_colours, key=distance)
        r2, g2, b2 = closest_colours[0]
        r = (r1 + r2) // 2
        g = (g1 + g2) // 2
        b = (b1 + b2) // 2

        return r, g, b

    @staticmethod
    def crop_avatar_circle(avatar: Image.Image) -> Image.Image:
        """This crops the avatar given into a circle."""
        mask = Image.new("L", avatar.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + avatar.size, fill=255)
        avatar.putalpha(mask)
        return avatar

    @staticmethod
    def crop_ring(ring: Image.Image, px: int) -> Image.Image:
        """This crops the given ring into a circle."""
        mask = Image.new("L", ring.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + ring.size, fill=255)
        draw.ellipse((px, px, 1024-px, 1024-px), fill=0)
        ring.putalpha(mask)
        return ring

    @staticmethod
    def pridify_effect(image: Image.Image, pixels: int, flag: str) -> Image.Image:
        """Applies the given pride effect to the given image."""
        image = PfpEffects.crop_avatar_circle(image)

        ring = Image.open(Path(f"bot/resources/holidays/pride/flags/{flag}.png")).resize((1024, 1024))
        ring = ring.convert("RGBA")
        ring = PfpEffects.crop_ring(ring, pixels)

        image.alpha_composite(ring, (0, 0))
        return image

    @staticmethod
    def eight_bitify_effect(image: Image.Image) -> Image.Image:
        """
        Applies the 8bit effect to the given image.

        This is done by reducing the image to 32x32 and then back up to 1024x1024.
        We then quantize the image before returning too.
        """
        image = image.resize((32, 32), resample=Image.NEAREST)
        image = image.resize((1024, 1024), resample=Image.NEAREST)
        return image.quantize()

    @staticmethod
    def flip_effect(image: Image.Image) -> Image.Image:
        """
        Flips the image horizontally.

        This is done by just using ImageOps.mirror().
        """
        image = ImageOps.mirror(image)

        return image

    @staticmethod
    def easterify_effect(image: Image.Image, overlay_image: Optional[Image.Image] = None) -> Image.Image:
        """
        Applies the easter effect to the given image.

        This is done by getting the closest "easter" colour to each pixel and changing the colour
        to the half-way RGB value.

        We also then add an overlay image on top in middle right, a chocolate bunny by default.
        """
        if overlay_image:
            ratio = 64 / overlay_image.height
            overlay_image = overlay_image.resize((
                round(overlay_image.width * ratio),
                round(overlay_image.height * ratio)
            ))
            overlay_image = overlay_image.convert("RGBA")
        else:
            overlay_image = Image.open(Path("bot/resources/holidays/easter/chocolate_bunny.png"))

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

    @staticmethod
    def split_image(img: Image.Image, squares: int) -> list:
        """
        Split an image into a selection of squares, specified by the squares argument.

        Explanation:

        1. It gets the width and the height of the Image passed to the function.

        2. It gets the root of a number of squares (number of squares) passed, which is called xy. Reason: if let's say
        25 squares (number of squares) were passed, that is the total squares (split pieces) that the image is supposed
        to be split into. As it is known, a 2D shape has a height and a width, and in this case the program thinks of it
        as rows and columns. Rows multiplied by columns is equal to the passed squares (number of squares). To get rows
        and columns, since in this case, each square (split piece) is identical, rows are equal to columns and the
        program treats the image as a square-shaped, it gets the root out of the squares (number of squares) passed.

        3. Now width and height are both of the original Image, Discord PFP, so when it comes to forming the squares,
        the program divides the original image's height and width by the xy. In a case of 25 squares (number of squares)
        passed, xy would be 5, so if an image was 250x300, x_frac would be 50 and y_frac - 60. Note:
        x_frac stands for a fracture of width. The reason it's called that is because it is shorter to use x for width
        in mind and then it's just half of the word fracture, same applies to y_frac, just height instead of width.
        x_frac and y_frac are width and height of a single square (split piece).

        4. With left, top, right, bottom, = 0, 0, x_frac, y_frac, the program sets these variables to create the initial
        square (split piece). Explanation: all of these 4 variables start at the top left corner of the Image, by adding
        value to right and bottom, it's creating the initial square (split piece).

        5. In the for loop, it keeps adding those squares (split pieces) in a row and once (index + 1) % xy == 0 is
        True, it adds to top and bottom to lower them and reset right and left to recreate the initial space between
        them, forming a square (split piece), it also adds the newly created square (split piece) into the new_imgs list
        where it stores them. The program keeps repeating this process till all 25 squares get added to the list.

        6. It returns new_imgs, a list of squares (split pieces).
        """
        width, heigth = img.size

        xy = math.sqrt(squares)

        x_frac = width // xy
        y_frac = heigth // xy

        left, top, right, bottom, = 0, 0, x_frac, y_frac

        new_imgs = []

        for index in range(squares):
            new_img = img.crop((left, top, right, bottom))
            new_imgs.append(new_img)

            if (index + 1) % xy == 0:
                top += y_frac
                bottom += y_frac
                left = 0
                right = x_frac
            else:
                left += x_frac
                right += x_frac

        return new_imgs

    @staticmethod
    def join_images(images: list[Image.Image]) -> Image.Image:
        """
        Stitches all the image squares into a new image.

        Explanation:

        1. Shuffles the passed images to randomize the pieces.

        2. The program gets a single square (split piece) out of the list and defines single_width as the square's width
        and single_height as the square's height.

        3. It gets the root of type integer of the number of images (split pieces) in the list and calls it multiplier.
        Program then proceeds to calculate total height and width of the new image that it's creating using the same
        multiplier.

        4. The program then defines new_image as the image that it's creating, using the previously obtained total_width
        and total_height.

        5. Now it defines width_multiplier as well as height with values of 0. These will be used to correctly position
        squares (split pieces) onto the new_image canvas.

        6. Similar to how in the split_image function, the program gets the root of number of images in the list.
        In split_image function, it was the passed squares (number of squares) instead of a number of imgs in the
        list that it got the square of here.

        7. In the for loop, as it iterates, the program multiplies single_width by width_multiplier to correctly
        position a square (split piece) width wise. It then proceeds to paste the newly positioned square (split piece)
        onto the new_image. The program increases the width_multiplier by 1 every iteration so the image wouldn't get
        pasted in the same spot and the positioning would move accordingly. It makes sure to increase the
        width_multiplier before the check, which checks if the end of a row has been reached, -
        (index + 1) % pieces == 0, so after it, if it was True, width_multiplier would have been reset to 0 (start of
        the row). If the check returns True, the height gets increased by a single square's (split piece) height to
        lower the positioning height wise and, as mentioned, the width_multiplier gets reset to 0 and width will
        then be calculated from the start of the new row. The for loop finishes once all the squares (split pieces) were
        positioned accordingly.

        8. Finally, it returns the new_image, the randomized squares (split pieces) stitched back into the format of the
        original image - user's PFP.
        """
        random.shuffle(images)
        single_img = images[0]

        single_wdith = single_img.size[0]
        single_height = single_img.size[1]

        multiplier = int(math.sqrt(len(images)))

        total_width = multiplier * single_wdith
        total_height = multiplier * single_height

        new_image = Image.new("RGBA", (total_width, total_height), (250, 250, 250))

        width_multiplier = 0
        height = 0

        squares = math.sqrt(len(images))

        for index, image in enumerate(images):
            width = single_wdith * width_multiplier

            new_image.paste(image, (width, height))

            width_multiplier += 1

            if (index + 1) % squares == 0:
                width_multiplier = 0
                height += single_height

        return new_image

    @staticmethod
    def mosaic_effect(image: Image.Image, squares: int) -> Image.Image:
        """
        Applies a mosaic effect to the given image.

        The "squares" argument specifies the number of squares to split
        the image into. This should be a square number.
        """
        img_squares = PfpEffects.split_image(image, squares)
        new_img = PfpEffects.join_images(img_squares)

        return new_img

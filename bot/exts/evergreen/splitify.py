import math
import random
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import discord
from PIL import Image
from discord.ext import commands


MAX_SQUARES = 193_600

EXECUTOR = ThreadPoolExecutor(10)


class Splitify(commands.Cog):
    """Splitifies your avatar!"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def split_image(img: Image.Image, squares: int) -> list:
        """
        Splits the image into x squares.

        Explanation:

        1. It gets the width and the height of the Image passed to the function.

        2. It gets the root of a number of squares (number of squares) passed, which is called xy. Reason: if let's say
        25 squares (number of squares) were passed, that is the total squares (split pieces) that the image is supposed
        to be split into. As it is known, a 2D shape has a height and a width, and in this case the program thinks of it
        as rows and columns. Rows multiplied by columns is equal to the passed squares (number of squares). To get rows
        and columns, since in this case, each square (split piece) is identical, rows are equal to columns and the
        program treats the image as a square-shaped, it gets the root out of the squares (number of squares) passed.

        3. Now width and height are both of the original Image, Discord PFP, so when it comes to forming the squares
        (splitpieces), the program divides the original image's height and width by the xy. In a case of 25 squares
        (number ofsquares) passed, xy would be 5, so if an image was 250x300, x_frac would be 50 and y_frac - 60. Note:
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
    def join_images(imgs: list) -> Image.Image:
        """
        Stitches all the image squares into a new image.

        Explanation:

        1. It shuffles passed imgs. Reason: to randomize the squares (split pieces).

        2. The program gets a single square (split piece) out of the list and defines single_width as the square's width
        and single_height as the square's height.

        3. It gets the root of type integer of the number of imgs (split pieces) in the list and calls it multiplier.
        Program then proceeds to calculate total height and width of the new image that it's creating using the same
        multiplier.

        4. The program then defines new_img as the image that it's creating, using the previously obtained total_width
        and total_height.

        5. Now it defines width_multiplier as well as height with values of 0. These will be used to correctly position
        squares (split pieces) onto the new_img canvas.

        6. Similar to how in the split_image function, the program gets the root of number of imgs (split pieces) in the
        list. In split_image function, it was the passed squares (number of squares) instead of a number of imgs in the
        list that it got the square of here.

        7. In the for loop, as it iterates, the program multiplies single_width by width_multiplier to correctly
        position a square (split piece) width wise. It then proceeds to paste the newly positioned square (split piece)
        onto the new_img. The program increases the width_multiplier by 1 every iteration so the image wouldn't get
        pasted in the same spot and the positioning would move accordingly. It makes sure to increase the
        width_multiplier before the check, which checks if the end of a row has been reached, -
        (index + 1) % pieces == 0, so after it, if it was True, width_multiplier would have been reset to 0 (start of
        the row). If the check returns True, the height gets increased by a single square's (split piece) height to
        lower the positioning height wise and, as I just mentioned, the width_multiplier gets reset to 0 and width will
        then be calculated from the start of the new row. The for loop finishes once all the squares (split pieces) were
        positioned accordingly.

        8. Finally, it returns the new_img, the randomized squares (split pieces) stitched back into the format of the
        original image - user's PFP.
        """
        random.shuffle(imgs)
        single_img = imgs[0]

        single_wdith = single_img.size[0]
        single_height = single_img.size[1]

        multiplier = int(math.sqrt(len(imgs)))

        total_width = multiplier * single_wdith
        total_height = multiplier * single_height

        new_img = Image.new('RGBA', (total_width, total_height), (250, 250, 250))

        width_multiplier = 0
        height = 0

        squares = math.sqrt(len(imgs))

        for index, img in enumerate(imgs):
            width = single_wdith * width_multiplier

            new_img.paste(img, (width, height))

            width_multiplier += 1

            if (index + 1) % squares == 0:
                width_multiplier = 0
                height += single_height

        return new_img

    def splitify(self, img_bytes: BytesIO, squares: int) -> BytesIO:
        """Seperate function run from an executor which splitifies an image."""
        avatar = Image.open(BytesIO(img_bytes))
        avatar = avatar.convert('RGBA').resize((1024, 1024))

        img_squares = self.split_image(avatar, squares)
        new_img = self.join_images(img_squares)

        bufferedio = BytesIO()
        new_img.save(bufferedio, format='PNG')
        bufferedio.seek(0)

        return bufferedio

    @commands.command(name='splitify')
    async def splitify_command(self, ctx: commands.Context, squares: int = 16) -> None:
        """Splits your avatar into x squares, randomizes them and stitches them back into a new image!"""
        async with ctx.typing():
            if squares < 1:
                raise commands.BadArgument('Squares must be a `positive number`:exclamation:')

            if not math.sqrt(squares).is_integer():
                raise commands.BadArgument('Squares must be a `perfect square`:exclamation:')

            if squares > MAX_SQUARES:
                raise commands.BadArgument('Number of squares cannot be higher than `193,600` :nerd:')

            img_bytes = await ctx.author.avatar_url.read()
            bufferedio = await self.bot.loop.run_in_executor(EXECUTOR, self.splitify, img_bytes, squares)

            file = discord.File(bufferedio, filename='splitifed.png')

            if squares == 1:
                title = 'Hooh... that was a lot of work'
                description = 'I present to you... Yourself!'
            elif squares == MAX_SQUARES:
                title = 'Testing the limits I see...'
                description = 'What a masterpiece. :star:'
            else:
                title = 'Your splitified avatar'
                description = 'Here is your avatar. I think it looks a bit *puzzly*'

            embed = discord.Embed(
                title=title,
                description=description
            )

            embed.set_image(url='attachment://splitifed.png')
            embed.set_footer(text=f'Made by {ctx.author.display_name}', icon_url=ctx.author.avatar_url)

            await ctx.send(file=file, embed=embed)


def setup(bot: commands.Bot) -> None:
    """Cog load."""
    bot.add_cog(Splitify(bot))

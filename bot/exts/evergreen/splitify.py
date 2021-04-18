import math
import random
from io import BytesIO

import discord
from PIL import Image
from discord.ext import commands


class Splitify(commands.Cog):
    """Splits your avatar in x squares!"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def split_image(img: Image, squares: int) -> list:
        """Splits the image into x squares."""
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
    def join_images(imgs: list) -> Image:
        """Stitches all the image squares into a new image."""
        random.shuffle(imgs)
        img_sizes = [img.size for img in imgs]

        single_wdith = img_sizes[0][0]
        single_height = img_sizes[0][1]

        multiplier = int(math.sqrt(len(imgs)))

        total_width = multiplier * single_wdith
        total_height = multiplier * single_height

        new_image = Image.new('RGBA', (total_width, total_height), (250, 250, 250))

        width_multiplier = 0
        height = 0

        pieces = math.sqrt(len(imgs))

        for index, img in enumerate(imgs):
            width = single_wdith * width_multiplier

            new_image.paste(img, (width, height))

            width_multiplier += 1

            if (index + 1) % pieces == 0:
                width_multiplier = 0
                height += single_height

        return new_image

    @commands.command(name='splitify')
    async def splitify_command(self, ctx: commands.Context, squares: int) -> None:
        """Splits your avatar in x squares, randomizes them and stitches them back into a new image!"""
        async with ctx.typing():
            squares = int(squares)

            if squares < 1:
                raise commands.BadArgument('Squares must be a `positive number`:exclamation:')

            if not math.sqrt(squares).is_integer():
                raise commands.BadArgument('Squares must be a `perfect square`:exclamation:')

            max_squares = 193_600

            if squares > max_squares:
                raise commands.BadArgument('Number of squares cannot be higher than `193,600` :nerd:')

            author = ctx.author
            image_bytes = await author.avatar_url.read()
            avatar = Image.open(BytesIO(image_bytes))
            avatar = avatar.convert('RGBA').resize((1024, 1024))

            img_squares = self.split_image(avatar, squares)
            new_img = self.join_images(img_squares)

            bufferedio = BytesIO()
            new_img.save(bufferedio, format='PNG')
            bufferedio.seek(0)

            file = discord.File(bufferedio, filename='splitifed.png')

            if squares == 1:
                title = 'Hooh... that was a lot of work'
                description = 'I present to you... Yourself!'
            elif squares == max_squares:
                title = 'Testing the limits I see...'
                description = 'What a masterpiece. :star:'
            else:
                title = 'Your splitified avatar'
                description = 'Here is your avatar. I think it looks a bit *puzzly*'

            embed = discord.Embed(title=title,
                                  description=description)

            embed.set_image(url='attachment://splitifed.png')
            embed.set_footer(text=f'Made by {ctx.author.display_name}', icon_url=ctx.author.avatar_url)

            await ctx.send(file=file, embed=embed)


def setup(bot: commands.Bot) -> None:
    """Cog load."""
    bot.add_cog(Splitify(bot))

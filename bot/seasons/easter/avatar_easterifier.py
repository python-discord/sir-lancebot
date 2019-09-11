import asyncio
import logging
from io import BytesIO
from pathlib import Path
from typing import Union

import discord
from PIL import Image
from PIL.ImageOps import posterize
from discord.ext import commands

log = logging.getLogger(__name__)

COLOURS = [
    (255, 247, 0), (255, 255, 224), (0, 255, 127), (189, 252, 201), (255, 192, 203),
    (255, 160, 122), (181, 115, 220), (221, 160, 221), (200, 162, 200), (238, 130, 238),
    (135, 206, 235), (0, 204, 204), (64, 224, 208)
]  # Pastel colours - Easter-like


class AvatarEasterifier(commands.Cog):
    """Put an Easter spin on your avatar or image!"""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def closest(x):
        """
        Finds the closest easter colour to a given pixel.

        Returns a merge between the original colour and the closest colour
        """
        r1, g1, b1 = x

        def distance(point):
            """Finds the difference between a pastel colour and the original pixel colour."""
            r2, g2, b2 = point
            return ((r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2)

        closest_colours = sorted(COLOURS, key=lambda point: distance(point))
        r2, g2, b2 = closest_colours[0]
        r = (r1 + r2) // 2
        g = (g1 + g2) // 2
        b = (b1 + b2) // 2

        return (r, g, b)

    @commands.command(pass_context=True, aliases=["easterify"])
    async def avatareasterify(self, ctx, *colours: Union[discord.Colour, str]):
        """
        This "Easterifies" the user's avatar.

        Given colours will produce a personalised egg in the corner, similar to the egg_decorate command.
        If colours are not given, a nice little chocolate bunny will sit in the corner.
        Colours are split by spaces, unless you wrap the colour name in double quotes.
        Discord colour names, HTML colour names, XKCD colour names and hex values are accepted.
        """
        async def send(*args, **kwargs):
            """
            This replaces the original ctx.send.

            When invoking the egg decorating command, the egg itself doesn't print to to the channel.
            Returns the message content so that if any errors occur, the error message can be output.
            """
            if args:
                return args[0]

        async with ctx.typing():

            # Grabs image of avatar
            image_bytes = await ctx.author.avatar_url_as(size=256).read()

            old = Image.open(BytesIO(image_bytes))
            old = old.convert("RGBA")

            # Grabs alpha channel since posterize can't be used with an RGBA image.
            alpha = old.getchannel("A").getdata()
            old = old.convert("RGB")
            old = posterize(old, 6)

            data = old.getdata()
            setted_data = set(data)
            new_d = {}

            for x in setted_data:
                new_d[x] = self.closest(x)
                await asyncio.sleep(0)  # Ensures discord doesn't break in the background.
            new_data = [(*new_d[x], alpha[i]) if x in new_d else x for i, x in enumerate(data)]

            im = Image.new("RGBA", old.size)
            im.putdata(new_data)

            if colours:
                send_message = ctx.send
                ctx.send = send  # Assigns ctx.send to a fake send
                egg = await ctx.invoke(self.bot.get_command("eggdecorate"), *colours)
                if isinstance(egg, str):  # When an error message occurs in eggdecorate.
                    return await send_message(egg)

                ratio = 64 / egg.height
                egg = egg.resize((round(egg.width * ratio), round(egg.height * ratio)))
                egg = egg.convert("RGBA")
                im.alpha_composite(egg, (im.width - egg.width, (im.height - egg.height)//2))  # Right centre.
                ctx.send = send_message  # Reassigns ctx.send
            else:
                bunny = Image.open(Path("bot/resources/easter/chocolate_bunny.png"))
                im.alpha_composite(bunny, (im.width - bunny.width, (im.height - bunny.height)//2))  # Right centre.

            bufferedio = BytesIO()
            im.save(bufferedio, format="PNG")

            bufferedio.seek(0)

            file = discord.File(bufferedio, filename="easterified_avatar.png")  # Creates file to be used in embed
            embed = discord.Embed(
                name="Your Lovely Easterified Avatar",
                description="Here is your lovely avatar, all bright and colourful\nwith Easter pastel colours. Enjoy :D"
            )
            embed.set_image(url="attachment://easterified_avatar.png")
            embed.set_footer(text=f"Made by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        await ctx.send(file=file, embed=embed)


def setup(bot):
    """Avatar Easterifier Cog load."""
    bot.add_cog(AvatarEasterifier(bot))
    log.info("AvatarEasterifier cog loaded")

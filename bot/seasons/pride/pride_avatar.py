import logging
from io import BytesIO
from pathlib import Path

import discord
from PIL import Image, ImageDraw
from discord.ext import commands

log = logging.getLogger(__name__)

OPTIONS = {
    "agender": "agender",
    "androgyne": "androgyne",
    "androgynous": "androgyne",
    "aromantic": "aromantic",
    "aro": "aromantic",
    "ace": "asexual",
    "asexual": "asexual",
    "bigender": "bigender",
    "bisexual": "bisexual",
    "bi": "bisexual",
    "demiboy": "demiboy",
    "demigirl": "demigirl",
    "demi": "demisexual",
    "demisexual": "demisexual",
    "gay": "gay",
    "lgbt": "gay",
    "queer": "gay",
    "homosexual": "gay",
    "fluid": "genderfluid",
    "genderfluid": "genderfluid",
    "genderqueer": "genderqueer",
    "intersex": "intersex",
    "lesbian": "lesbian",
    "non-binary": "nonbinary",
    "enby": "nonbinary",
    "nb": "nonbinary",
    "nonbinary": "nonbinary",
    "omnisexual": "omnisexual",
    "omni": "omnisexual",
    "pansexual": "pansexual",
    "pan": "pansexual",
    "pangender": "pangender",
    "poly": "polysexual",
    "polysexual": "polysexual",
    "polyamory": "polyamory",
    "polyamorous": "polyamory",
    "transgender": "transgender",
    "trans": "transgender",
    "trigender": "trigender"
}


class PrideAvatar(commands.Cog):
    """Put an LGBT spin on your avatar!"""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def crop_avatar(avatar):
        """This crops the avatar into a circle."""

        mask = Image.new("L", avatar.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + avatar.size, fill=255)
        avatar.putalpha(mask)
        return avatar

    @staticmethod
    def crop_ring(ring, px):
        """This crops the ring into a circle."""

        mask = Image.new("L", ring.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + ring.size, fill=255)
        draw.ellipse((px, px, 1024-px, 1024-px), fill=0)
        ring.putalpha(mask)
        return ring

    @commands.command(aliases=["avatarpride", "pridepfp", "prideprofile"])
    async def prideavatar(self, ctx, option="lgbt", pixels: int = 64):
        """
        This surrounds an avatar with a border of a specified LGBT flag.

        This defaults to the LGBT rainbow flag if none is given.
        The amount of pixels can be given which determines the thickness of the flag border.
        This has a maximum of 512px and defaults to a 64px border.
        The full image is 1024x1024.
        """

        pixels = 0 if pixels < 0 else 512 if pixels > 512 else pixels

        option = option.lower()

        if option not in OPTIONS.keys():
            return await ctx.send("I don't have that flag!")

        flag = OPTIONS[option]

        async with ctx.typing():

            # Get avatar bytes
            image_bytes = await ctx.author.avatar_url.read()
            avatar = Image.open(BytesIO(image_bytes))
            avatar = avatar.convert("RGBA").resize((1024, 1024))

            avatar = self.crop_avatar(avatar)

            ring = Image.open(Path("bot", "resources", "pride", "flags", f"{flag}.png")).resize((1024, 1024))
            ring = self.crop_ring(ring, pixels)

            avatar.alpha_composite(ring, (0, 0))
            bufferedio = BytesIO()
            avatar.save(bufferedio, format="PNG")
            bufferedio.seek(0)

            file = discord.File(bufferedio, filename="pride_avatar.png")  # Creates file to be used in embed
            embed = discord.Embed(
                name="Your Lovely Pride Avatar",
                description=f"Here is your lovely avatar, surrounded by\n a beautiful {option} flag. Enjoy :D"
            )
            embed.set_image(url="attachment://pride_avatar.png")
            embed.set_footer(text=f"Made by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        await ctx.send(file=file, embed=embed)


def setup(bot):
    """Cog load."""

    bot.add_cog(PrideAvatar(bot))
    log.info("PrideAvatar cog loaded")

import logging
from io import BytesIO
from pathlib import Path
from typing import Optional

import aiohttp
import discord
from PIL import Image, ImageDraw, UnidentifiedImageError
from discord.ext.commands import Bot, Cog, Context, group

from bot.constants import Colours

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


class PrideAvatar(Cog):
    """Put an LGBT spin on your avatar!"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def crop_avatar(avatar: Image) -> Image:
        """This crops the avatar into a circle."""
        mask = Image.new("L", avatar.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + avatar.size, fill=255)
        avatar.putalpha(mask)
        return avatar

    @staticmethod
    def crop_ring(ring: Image, px: int) -> Image:
        """This crops the ring into a circle."""
        mask = Image.new("L", ring.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + ring.size, fill=255)
        draw.ellipse((px, px, 1024-px, 1024-px), fill=0)
        ring.putalpha(mask)
        return ring

    @staticmethod
    def process_options(option: str, pixels: int) -> tuple[str, int, Optional[str]]:
        """Does some shared preprocessing for the prideavatar commands."""
        return option.lower(), max(0, min(512, pixels)), OPTIONS.get(option)

    async def process_image(self, ctx: Context, image_bytes: bytes, pixels: int, flag: str, option: str) -> None:
        """Constructs the final image, embeds it, and sends it."""
        try:
            avatar = Image.open(BytesIO(image_bytes))
        except UnidentifiedImageError:
            return await ctx.send("Cannot identify image from provided URL")
        avatar = avatar.convert("RGBA").resize((1024, 1024))

        avatar = self.crop_avatar(avatar)

        ring = Image.open(Path(f"bot/resources/pride/flags/{flag}.png")).resize((1024, 1024))
        ring = ring.convert("RGBA")
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

    @group(aliases=["avatarpride", "pridepfp", "prideprofile"], invoke_without_command=True)
    async def prideavatar(self, ctx: Context, option: str = "lgbt", pixels: int = 64) -> None:
        """
        This surrounds an avatar with a border of a specified LGBT flag.

        This defaults to the LGBT rainbow flag if none is given.
        The amount of pixels can be given which determines the thickness of the flag border.
        This has a maximum of 512px and defaults to a 64px border.
        The full image is 1024x1024.
        """
        option, pixels, flag = self.process_options(option, pixels)
        if flag is None:
            return await ctx.send("I don't have that flag!")

        async with ctx.typing():
            image_bytes = await ctx.author.avatar_url.read()
            await self.process_image(ctx, image_bytes, pixels, flag, option)

    @prideavatar.command()
    async def image(self, ctx: Context, url: str, option: str = "lgbt", pixels: int = 64) -> None:
        """
        This surrounds the image specified by the URL with a border of a specified LGBT flag.

        This defaults to the LGBT rainbow flag if none is given.
        The amount of pixels can be given which determines the thickness of the flag border.
        This has a maximum of 512px and defaults to a 64px border.
        The full image is 1024x1024.
        """
        option, pixels, flag = self.process_options(option, pixels)
        if flag is None:
            return await ctx.send("I don't have that flag!")

        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                try:
                    response = await session.get(url)
                except aiohttp.client_exceptions.ClientConnectorError:
                    return await ctx.send("Cannot connect to provided URL!")
                except aiohttp.client_exceptions.InvalidURL:
                    return await ctx.send("Invalid URL!")
                if response.status != 200:
                    return await ctx.send("Bad response from provided URL!")
                image_bytes = await response.read()
                await self.process_image(ctx, image_bytes, pixels, flag, option)

    @prideavatar.command()
    async def flags(self, ctx: Context) -> None:
        """This lists the flags that can be used with the prideavatar command."""
        choices = sorted(set(OPTIONS.values()))
        options = "• " + "\n• ".join(choices)
        embed = discord.Embed(
            title="I have the following flags:",
            description=options,
            colour=Colours.soft_red
        )

        await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Cog load."""
    bot.add_cog(PrideAvatar(bot))

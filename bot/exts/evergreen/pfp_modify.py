import asyncio
import json
import logging
import typing as t
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import aiofiles
import discord
from PIL import Image, ImageDraw, ImageOps
from aiohttp import client_exceptions
from discord.ext import commands

from bot.constants import Colours
from bot.utils.halloween import spookifications

log = logging.getLogger(__name__)

EASTER_COLOURS = [
    (255, 247, 0), (255, 255, 224), (0, 255, 127), (189, 252, 201), (255, 192, 203),
    (255, 160, 122), (181, 115, 220), (221, 160, 221), (200, 162, 200), (238, 130, 238),
    (135, 206, 235), (0, 204, 204), (64, 224, 208)
]  # Pastel colours - Easter-like

_EXECUTOR = ThreadPoolExecutor(10)


async def in_thread(func: t.Callable, *args) -> asyncio.Future:
    """Allows non-async functions to work in async functions."""
    log.trace(f"Running {func.__name__} in an executor.")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_EXECUTOR, func, *args)


class PfpModify(commands.Cog):
    """Various commands for users to change their own profile picture."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.bot.loop.create_task(self.init_cog())

    async def init_cog(self) -> None:
        """Initial load from resources asynchronously."""
        async with aiofiles.open('bot/resources/pride/gender_options.json') as f:
            self.GENDER_OPTIONS = json.loads(await f.read())

    @staticmethod
    def closest(x: t.Tuple[int, int, int]) -> t.Tuple[int, int, int]:
        """
        Finds the closest easter colour to a given pixel.

        Returns a merge between the original colour and the closest colour
        """
        r1, g1, b1 = x

        def distance(point: t.Tuple[int, int, int]) -> t.Tuple[int, int, int]:
            """Finds the difference between a pastel colour and the original pixel colour."""
            r2, g2, b2 = point
            return ((r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2)

        closest_colours = sorted(EASTER_COLOURS, key=lambda point: distance(point))
        r2, g2, b2 = closest_colours[0]
        r = (r1 + r2) // 2
        g = (g1 + g2) // 2
        b = (b1 + b2) // 2

        return (r, g, b)

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
    def _apply_effect(image_bytes: bytes, effect: t.Callable, *args) -> discord.File:
        im = Image.open(BytesIO(image_bytes))
        im = im.convert("RGBA")
        im = effect(im, *args)

        bufferedio = BytesIO()
        im.save(bufferedio, format="PNG")
        bufferedio.seek(0)

        return discord.File(bufferedio, filename="modified_avatar.png")

    @staticmethod
    def pridify_effect(
        image: Image,
        pixels: int,
        flag: str
    ) -> Image:
        """Applies the pride effect to the given image."""
        image = image.resize((1024, 1024))
        image = PfpModify.crop_avatar_circle(image)

        ring = Image.open(Path(f"bot/resources/pride/flags/{flag}.png")).resize((1024, 1024))
        ring = ring.convert("RGBA")
        ring = PfpModify.crop_ring(ring, pixels)

        image.alpha_composite(ring, (0, 0))
        return image

    @staticmethod
    def eight_bitify_effect(image: Image) -> Image:
        """Applies the 8bit effect to the given image."""
        image = image.resize((32, 32), resample=Image.NEAREST).resize((1024, 1024), resample=Image.NEAREST)
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
        setted_data = set(data)
        new_d = {}

        for x in setted_data:
            new_d[x] = PfpModify.closest(x)
        new_data = [(*new_d[x], alpha[i]) if x in new_d else x for i, x in enumerate(data)]

        im = Image.new("RGBA", image.size)
        im.putdata(new_data)
        im.alpha_composite(overlay_image, (im.width - overlay_image.width, (im.height - overlay_image.height)//2))
        return im

    @commands.group()
    async def pfp_modify(self, ctx: commands.Context) -> None:
        """Groups all of the pfp modifing commands to allow a single concurrency limit."""
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @pfp_modify.command(name="8bitify", root_aliases=("8bitify",))
    async def eightbit_command(self, ctx: commands.Context) -> None:
        """Pixelates your avatar and changes the palette to an 8bit one."""
        async with ctx.typing():
            image_bytes = await ctx.author.avatar_url.read()
            file = await in_thread(
                self._apply_effect,
                image_bytes,
                self.eight_bitify_effect
            )

            embed = discord.Embed(
                title="Your 8-bit avatar",
                description='Here is your avatar. I think it looks all cool and "retro"'
            )

            embed.set_image(url="attachment://modified_avatar.png")
            embed.set_footer(text=f"Made by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        await ctx.send(file=file, embed=embed)

    @pfp_modify.command(pass_context=True, aliases=["easterify"], root_aliases=("easterify", "avatareasterify"))
    async def avatareasterify(self, ctx: commands.Context, *colours: t.Union[discord.Colour, str]) -> None:
        """
        This "Easterifies" the user's avatar.

        Given colours will produce a personalised egg in the corner, similar to the egg_decorate command.
        If colours are not given, a nice little chocolate bunny will sit in the corner.
        Colours are split by spaces, unless you wrap the colour name in double quotes.
        Discord colour names, HTML colour names, XKCD colour names and hex values are accepted.
        """
        async def send(*args, **kwargs) -> str:
            """
            This replaces the original ctx.send.

            When invoking the egg decorating command, the egg itself doesn't print to to the channel.
            Returns the message content so that if any errors occur, the error message can be output.
            """
            if args:
                return args[0]

        async with ctx.typing():
            egg = None
            if colours:
                send_message = ctx.send
                ctx.send = send  # Assigns ctx.send to a fake send
                egg = await ctx.invoke(self.bot.get_command("eggdecorate"), *colours)
                if isinstance(egg, str):  # When an error message occurs in eggdecorate.
                    await send_message(egg)
                    return
                ctx.send = send_message  # Reassigns ctx.send

            image_bytes = await ctx.author.avatar_url_as(size=256).read()
            file = await in_thread(
                self._apply_effect,
                image_bytes,
                self.easterify_effect,
                egg
            )

            embed = discord.Embed(
                name="Your Lovely Easterified Avatar",
                description="Here is your lovely avatar, all bright and colourful\nwith Easter pastel colours. Enjoy :D"
            )
            embed.set_image(url="attachment://modified_avatar.png")
            embed.set_footer(text=f"Made by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        await ctx.send(file=file, embed=embed)

    async def send_pride_image(
        self,
        ctx: commands.Context,
        image_bytes: bytes,
        pixels: int,
        flag: str,
        option: str
    ) -> None:
        """Gets and sends the image in an embed. Used by the pride commands."""
        async with ctx.typing():
            file = await in_thread(
                self._apply_effect,
                image_bytes,
                self.pridify_effect,
                pixels,
                flag
            )

            embed = discord.Embed(
                name="Your Lovely Pride Avatar",
                description=f"Here is your lovely avatar, surrounded by\n a beautiful {option} flag. Enjoy :D"
            )
            embed.set_image(url="attachment://modified_avatar.png")
            embed.set_footer(text=f"Made by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
            await ctx.send(file=file, embed=embed)

    @pfp_modify.group(
        aliases=["avatarpride", "pridepfp", "prideprofile"],
        root_aliases=("prideavatar", "avatarpride", "pridepfp", "prideprofile"),
        invoke_without_command=True
    )
    async def prideavatar(self, ctx: commands.Context, option: str = "lgbt", pixels: int = 64) -> None:
        """
        This surrounds an avatar with a border of a specified LGBT flag.

        This defaults to the LGBT rainbow flag if none is given.
        The amount of pixels can be given which determines the thickness of the flag border.
        This has a maximum of 512px and defaults to a 64px border.
        The full image is 1024x1024.
        """
        option = option.lower()
        pixels = max(0, min(512, pixels))
        flag = self.GENDER_OPTIONS.get(option)
        if flag is None:
            return await ctx.send("I don't have that flag!")

        async with ctx.typing():
            image_bytes = await ctx.author.avatar_url.read()
            await self.send_pride_image(ctx, image_bytes, pixels, flag, option)

    @prideavatar.command()
    async def image(self, ctx: commands.Context, url: str, option: str = "lgbt", pixels: int = 64) -> None:
        """
        This surrounds the image specified by the URL with a border of a specified LGBT flag.

        This defaults to the LGBT rainbow flag if none is given.
        The amount of pixels can be given which determines the thickness of the flag border.
        This has a maximum of 512px and defaults to a 64px border.
        The full image is 1024x1024.
        """
        option = option.lower()
        pixels = max(0, min(512, pixels))
        flag = self.GENDER_OPTIONS.get(option)
        if flag is None:
            return await ctx.send("I don't have that flag!")

        async with ctx.typing():
            async with self.bot.http_session as session:
                try:
                    response = await session.get(url)
                except client_exceptions.ClientConnectorError:
                    return await ctx.send("Cannot connect to provided URL!")
                except client_exceptions.InvalidURL:
                    return await ctx.send("Invalid URL!")
                if response.status != 200:
                    return await ctx.send("Bad response from provided URL!")
                image_bytes = await response.read()
                await self.send_pride_image(ctx, image_bytes, pixels, flag, option)

    @prideavatar.command()
    async def flags(self, ctx: commands.Context) -> None:
        """This lists the flags that can be used with the prideavatar command."""
        choices = sorted(set(self.GENDER_OPTIONS.values()))
        options = "• " + "\n• ".join(choices)
        embed = discord.Embed(
            title="I have the following flags:",
            description=options,
            colour=Colours.soft_red
        )
        await ctx.send(embed=embed)

    @pfp_modify.command(
        name='savatar',
        aliases=('spookyavatar', 'spookify'),
        root_aliases=('spookyavatar', 'spookify'),
        brief='Spookify an user\'s avatar.'
    )
    async def spooky_avatar(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """A command to print the user's spookified avatar."""
        if user is None:
            user = ctx.message.author

        async with ctx.typing():
            image_bytes = await ctx.author.avatar_url.read()
            file = await in_thread(self._apply_effect, image_bytes, spookifications.get_random_effect)

            embed = discord.Embed(
                title="Is this you or am I just really paranoid?",
                colour=0xFF0000
            )
            embed.set_author(name=str(user.name), icon_url=user.avatar_url)
            embed.set_image(url='attachment://modified_avatar.png')
            embed.set_footer(text=f"Made by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

            await ctx.send(file=file, embed=embed)


def setup(bot: commands.Bot) -> None:
    """Load the PfpModify cog."""
    bot.add_cog(PfpModify(bot))

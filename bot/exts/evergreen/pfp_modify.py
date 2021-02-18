import asyncio
import json
import logging
import os
import typing as t
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import aiofiles
import aiohttp
import discord
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError
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
    def crop_avatar(avatar: Image) -> Image:
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

    def process_options(self, option: str, pixels: int) -> t.Tuple[str, int, str]:
        """Does some shared preprocessing for the prideavatar commands."""
        return option.lower(), max(0, min(512, pixels)), self.GENDER_OPTIONS.get(option)

    def process_image(
        self,
        image_bytes: bytes,
        pixels: int,
        flag: str
    ) -> discord.File:
        """Constructs and returns the final image. Used by the pride commands."""
        # This line can raise UnidentifiedImageError and must be handled by the calling func.
        avatar = Image.open(BytesIO(image_bytes))
        avatar = avatar.convert("RGBA").resize((1024, 1024))

        avatar = self.crop_avatar(avatar)

        ring = Image.open(Path(f"bot/resources/pride/flags/{flag}.png")).resize((1024, 1024))
        ring = ring.convert("RGBA")
        ring = self.crop_ring(ring, pixels)

        avatar.alpha_composite(ring, (0, 0))
        bufferedio = BytesIO()
        avatar.save(bufferedio, format="PNG")
        bufferedio.seek(0)

        return discord.File(bufferedio, filename="pride_avatar.png")  # Creates file to be used in embed

    async def send_image(
        self,
        ctx: commands.Context,
        image_bytes: bytes,
        pixels: int,
        flag: str,
        option: str
    ) -> None:
        """Gets and sends the image in an embed. Used by the pride commands."""
        try:
            file = await in_thread(self.process_image, image_bytes, pixels, flag)
        except UnidentifiedImageError:
            ctx.send("Cannot identify image from provided URL")
            return

        embed = discord.Embed(
            name="Your Lovely Pride Avatar",
            description=f"Here is your lovely avatar, surrounded by\n a beautiful {option} flag. Enjoy :D"
        )
        embed.set_image(url="attachment://pride_avatar.png")
        embed.set_footer(text=f"Made by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        await ctx.send(file=file, embed=embed)

    @commands.max_concurrency(1, commands.BucketType.guild, wait=True)
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
            avatar = Image.open(BytesIO(image_bytes))
            avatar = avatar.convert("RGBA").resize((1024, 1024))

            # Pixilate and quantize
            eightbit = avatar.resize((32, 32), resample=Image.NEAREST).resize((1024, 1024), resample=Image.NEAREST)
            eightbit = eightbit.quantize()

            bufferedio = BytesIO()
            eightbit.save(bufferedio, format="PNG")
            bufferedio.seek(0)

            file = discord.File(bufferedio, filename="8bitavatar.png")

            embed = discord.Embed(
                title="Your 8-bit avatar",
                description='Here is your avatar. I think it looks all cool and "retro"'
            )

            embed.set_image(url="attachment://8bitavatar.png")
            embed.set_footer(text=f"Made by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        await ctx.send(file=file, embed=embed)

    @pfp_modify.command(pass_context=True, aliases=["easterify"])
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

            # Grabs image of avatar
            image_bytes = await ctx.author.avatar_url_as(size=256).read()

            old = Image.open(BytesIO(image_bytes))
            old = old.convert("RGBA")

            # Grabs alpha channel since posterize can't be used with an RGBA image.
            alpha = old.getchannel("A").getdata()
            old = old.convert("RGB")
            old = ImageOps.posterize(old, 6)

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

    @pfp_modify.group(aliases=["avatarpride", "pridepfp", "prideprofile"], invoke_without_command=True)
    async def prideavatar(self, ctx: commands.Context, option: str = "lgbt", pixels: int = 64) -> None:
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
            await self.send_image(ctx, image_bytes, pixels, flag, option)

    @prideavatar.command()
    async def image(self, ctx: commands.Context, url: str, option: str = "lgbt", pixels: int = 64) -> None:
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
                await self.send_image(ctx, image_bytes, pixels, flag, option)

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
        brief='Spookify an user\'s avatar.'
    )
    async def spooky_avatar(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """A command to print the user's spookified avatar."""
        if user is None:
            user = ctx.message.author

        async with ctx.typing():
            embed = discord.Embed(colour=0xFF0000)
            embed.title = "Is this you or am I just really paranoid?"
            embed.set_author(name=str(user.name), icon_url=user.avatar_url)

            image_bytes = await ctx.author.avatar_url.read()
            im = Image.open(BytesIO(image_bytes))
            modified_im = spookifications.get_random_effect(im)
            modified_im.save(str(ctx.message.id)+'.png')
            f = discord.File(str(ctx.message.id)+'.png')
            embed.set_image(url='attachment://'+str(ctx.message.id)+'.png')

        await ctx.send(file=f, embed=embed)
        os.remove(str(ctx.message.id)+'.png')


def setup(bot: commands.Bot) -> None:
    """Load the PfpModify cog."""
    bot.add_cog(PfpModify(bot))

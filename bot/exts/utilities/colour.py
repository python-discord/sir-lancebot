import colorsys
import json
import pathlib
import random
import string
from io import BytesIO
from typing import Optional

import discord
import rapidfuzz
from PIL import Image, ImageColor
from discord.ext import commands

from bot import constants
from bot.bot import Bot
from bot.utils.decorators import whitelist_override

THUMBNAIL_SIZE = (80, 80)


class Colour(commands.Cog):
    """Cog for the Colour command."""

    def __init__(self, bot: Bot):
        self.bot = bot
        with open(pathlib.Path("bot/resources/utilities/ryanzec_colours.json")) as f:
            self.colour_mapping = json.load(f)
            del self.colour_mapping['_']  # Delete source credit entry

    async def send_colour_response(self, ctx: commands.Context, rgb: tuple[int, int, int]) -> None:
        """Create and send embed from user given colour information."""
        name = self._rgb_to_name(rgb)
        try:
            colour_or_color = ctx.invoked_parents[0]
        except IndexError:
            colour_or_color = "colour"

        colour_mode = ctx.invoked_with
        if colour_mode == "random":
            colour_mode = colour_or_color
            input_colour = name
        elif colour_mode in ("colour", "color"):
            input_colour = ctx.kwargs["colour_input"]
        elif colour_mode == "name":
            input_colour = ctx.kwargs["user_colour_name"]
        elif colour_mode == "hex":
            input_colour = ctx.args[2:][0]
            if len(input_colour) > 7:
                input_colour = input_colour[0:-2]
        else:
            input_colour = tuple(ctx.args[2:])

        if colour_mode not in ("name", "hex", "random", "color", "colour"):
            colour_mode = colour_mode.upper()
        else:
            colour_mode = colour_mode.title()

        colour_embed = discord.Embed(
            title=f"{name or input_colour}",
            description=f"{colour_or_color.title()} information for {colour_mode} `{input_colour or name}`.",
            colour=discord.Color.from_rgb(*rgb)
        )
        colour_conversions = self.get_colour_conversions(rgb)
        for colour_space, value in colour_conversions.items():
            colour_embed.add_field(
                name=colour_space,
                value=f"`{value}`",
                inline=True
            )

        thumbnail = Image.new("RGB", THUMBNAIL_SIZE, color=rgb)
        buffer = BytesIO()
        thumbnail.save(buffer, "PNG")
        buffer.seek(0)
        thumbnail_file = discord.File(buffer, filename="colour.png")

        colour_embed.set_thumbnail(url="attachment://colour.png")

        await ctx.send(file=thumbnail_file, embed=colour_embed)

    @commands.group(aliases=("color",), invoke_without_command=True)
    @whitelist_override(
        channels=constants.WHITELISTED_CHANNELS,
        roles=constants.STAFF_ROLES,
        categories=[constants.Categories.development, constants.Categories.media]
    )
    async def colour(self, ctx: commands.Context, *, colour_input: Optional[str] = None) -> None:
        """
        Create an embed that displays colour information.

        If no subcommand is called, a randomly selected colour will be shown.
        """
        if colour_input is None:
            await self.random(ctx)
            return

        try:
            extra_colour = ImageColor.getrgb(colour_input)
            await self.send_colour_response(ctx, extra_colour)
        except ValueError:
            await self.bot.invoke_help_command(ctx)

    @colour.command()
    async def rgb(self, ctx: commands.Context, red: int, green: int, blue: int) -> None:
        """Create an embed from an RGB input."""
        if any(c not in range(256) for c in (red, green, blue)):
            raise commands.BadArgument(
                message=f"RGB values can only be from 0 to 255. User input was: `{red, green, blue}`."
            )
        rgb_tuple = (red, green, blue)
        await self.send_colour_response(ctx, rgb_tuple)

    @colour.command()
    async def hsv(self, ctx: commands.Context, hue: int, saturation: int, value: int) -> None:
        """Create an embed from an HSV input."""
        if (hue not in range(361)) or any(c not in range(101) for c in (saturation, value)):
            raise commands.BadArgument(
                message="Hue can only be from 0 to 360. Saturation and Value can only be from 0 to 100. "
                f"User input was: `{hue, saturation, value}`."
            )
        hsv_tuple = ImageColor.getrgb(f"hsv({hue}, {saturation}%, {value}%)")
        await self.send_colour_response(ctx, hsv_tuple)

    @colour.command()
    async def hsl(self, ctx: commands.Context, hue: int, saturation: int, lightness: int) -> None:
        """Create an embed from an HSL input."""
        if (hue not in range(361)) or any(c not in range(101) for c in (saturation, lightness)):
            raise commands.BadArgument(
                message="Hue can only be from 0 to 360. Saturation and Lightness can only be from 0 to 100. "
                f"User input was: `{hue, saturation, lightness}`."
            )
        hsl_tuple = ImageColor.getrgb(f"hsl({hue}, {saturation}%, {lightness}%)")
        await self.send_colour_response(ctx, hsl_tuple)

    @colour.command()
    async def cmyk(self, ctx: commands.Context, cyan: int, magenta: int, yellow: int, key: int) -> None:
        """Create an embed from a CMYK input."""
        if any(c not in range(101) for c in (cyan, magenta, yellow, key)):
            raise commands.BadArgument(
                message=f"CMYK values can only be from 0 to 100. User input was: `{cyan, magenta, yellow, key}`."
            )
        r = round(255 * (1 - (cyan / 100)) * (1 - (key / 100)))
        g = round(255 * (1 - (magenta / 100)) * (1 - (key / 100)))
        b = round(255 * (1 - (yellow / 100)) * (1 - (key / 100)))
        await self.send_colour_response(ctx, (r, g, b))

    @colour.command()
    async def hex(self, ctx: commands.Context, hex_code: str) -> None:
        """Create an embed from a HEX input."""
        if hex_code[0] != "#":
            hex_code = f"#{hex_code}"

        if len(hex_code) not in (4, 5, 7, 9) or any(digit not in string.hexdigits for digit in hex_code[1:]):
            raise commands.BadArgument(
                message=f"Cannot convert `{hex_code}` to a recognizable Hex format. "
                "Hex values must be hexadecimal and take the form *#RRGGBB* or *#RGB*."
            )

        hex_tuple = ImageColor.getrgb(hex_code)
        if len(hex_tuple) == 4:
            hex_tuple = hex_tuple[:-1]  # Colour must be RGB. If RGBA, we remove the alpha value
        await self.send_colour_response(ctx, hex_tuple)

    @colour.command()
    async def name(self, ctx: commands.Context, *, user_colour_name: str) -> None:
        """Create an embed from a name input."""
        hex_colour = self.match_colour_name(ctx, user_colour_name)
        if hex_colour is None:
            name_error_embed = discord.Embed(
                title="No colour match found.",
                description=f"No colour found for: `{user_colour_name}`",
                colour=discord.Color.dark_red()
            )
            await ctx.send(embed=name_error_embed)
            return
        hex_tuple = ImageColor.getrgb(hex_colour)
        await self.send_colour_response(ctx, hex_tuple)

    @colour.command()
    async def random(self, ctx: commands.Context) -> None:
        """Create an embed from a randomly chosen colour."""
        hex_colour = random.choice(list(self.colour_mapping.values()))
        hex_tuple = ImageColor.getrgb(f"#{hex_colour}")
        await self.send_colour_response(ctx, hex_tuple)

    def get_colour_conversions(self, rgb: tuple[int, int, int]) -> dict[str, str]:
        """Create a dictionary mapping of colour types and their values."""
        colour_name = self._rgb_to_name(rgb)
        if colour_name is None:
            colour_name = "No match found"
        return {
            "RGB": rgb,
            "HSV": self._rgb_to_hsv(rgb),
            "HSL": self._rgb_to_hsl(rgb),
            "CMYK": self._rgb_to_cmyk(rgb),
            "Hex": self._rgb_to_hex(rgb),
            "Name": colour_name
        }

    @staticmethod
    def _rgb_to_hsv(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
        """Convert RGB values to HSV values."""
        rgb_list = [val / 255 for val in rgb]
        h, s, v = colorsys.rgb_to_hsv(*rgb_list)
        hsv = (round(h * 360), round(s * 100), round(v * 100))
        return hsv

    @staticmethod
    def _rgb_to_hsl(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
        """Convert RGB values to HSL values."""
        rgb_list = [val / 255.0 for val in rgb]
        h, l, s = colorsys.rgb_to_hls(*rgb_list)
        hsl = (round(h * 360), round(s * 100), round(l * 100))
        return hsl

    @staticmethod
    def _rgb_to_cmyk(rgb: tuple[int, int, int]) -> tuple[int, int, int, int]:
        """Convert RGB values to CMYK values."""
        rgb_list = [val / 255.0 for val in rgb]
        if not any(rgb_list):
            return 0, 0, 0, 100
        k = 1 - max(rgb_list)
        c = round((1 - rgb_list[0] - k) * 100 / (1 - k))
        m = round((1 - rgb_list[1] - k) * 100 / (1 - k))
        y = round((1 - rgb_list[2] - k) * 100 / (1 - k))
        cmyk = (c, m, y, round(k * 100))
        return cmyk

    @staticmethod
    def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        """Convert RGB values to HEX code."""
        hex_ = "".join([hex(val)[2:].zfill(2) for val in rgb])
        hex_code = f"#{hex_}".upper()
        return hex_code

    def _rgb_to_name(self, rgb: tuple[int, int, int]) -> Optional[str]:
        """Convert RGB values to a fuzzy matched name."""
        input_hex_colour = self._rgb_to_hex(rgb)
        try:
            match, certainty, _ = rapidfuzz.process.extractOne(
                query=input_hex_colour,
                choices=self.colour_mapping.values(),
                score_cutoff=80
            )
            colour_name = [name for name, hex_code in self.colour_mapping.items() if hex_code == match][0]
        except TypeError:
            colour_name = None
        return colour_name

    def match_colour_name(self, ctx: commands.Context, input_colour_name: str) -> Optional[str]:
        """Convert a colour name to HEX code."""
        try:
            match, certainty, _ = rapidfuzz.process.extractOne(
                query=input_colour_name,
                choices=self.colour_mapping.keys(),
                score_cutoff=80
            )
        except (ValueError, TypeError):
            return
        return f"#{self.colour_mapping[match]}"


def setup(bot: Bot) -> None:
    """Load the Colour cog."""
    bot.add_cog(Colour(bot))

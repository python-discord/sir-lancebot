import colorsys
import json
import pathlib
import random
from io import BytesIO

from PIL import Image, ImageColor
from discord import Embed, File
from discord.ext import commands
from discord.ext.commands.errors import BadArgument
from rapidfuzz import process

from bot.bot import Bot
from bot.exts.core.extensions import invoke_help_command

THUMBNAIL_SIZE = (80, 80)


class Colour(commands.Cog):
    """Cog for the Colour command."""

    def __init__(self, bot: Bot):
        self.bot = bot
        with open(pathlib.Path("bot/resources/utilities/ryanzec_colours.json")) as f:
            self.colour_mapping = json.load(f)

    async def send_colour_response(self, ctx: commands.Context, rgb: tuple[int, int, int]) -> None:
        """Create and send embed from user given colour information."""
        r, g, b = rgb
        name = self._rgb_to_name(rgb)
        if name == "No match found":
            name = None

        try:
            colour_or_color = ctx.invoked_parents[0]
        except IndexError:
            colour_or_color = "colour"

        colour_mode = ctx.invoked_with
        if colour_mode == "random":
            input_colour = "random"
        elif colour_mode in ("colour", "color"):
            input_colour = rgb
        else:
            input_colour = ctx.args[2:][0]

        if colour_mode not in ("name", "hex", "random", "color", "colour"):
            colour_mode = colour_mode.upper()
        else:
            colour_mode = colour_mode.title()

        desc = f"{colour_mode} information for `{name or input_colour}`."
        colour_embed = Embed(
            title=colour_or_color.title(),
            description=desc,
            colour=int(f"{r:02x}{g:02x}{b:02x}", 16)
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
        thumbnail_file = File(buffer, filename="colour.png")

        colour_embed.set_thumbnail(url="attachment://colour.png")

        await ctx.send(file=thumbnail_file, embed=colour_embed)

    @commands.group(aliases=("color",), invoke_without_command=True)
    async def colour(self, ctx: commands.Context, *, extra: str) -> None:
        """User initiated command to create an embed that displays colour information."""
        if ctx.invoked_subcommand is None:
            try:
                extra_colour = ImageColor.getrgb(extra)
                await self.send_colour_response(ctx, extra_colour)
            except ValueError:
                await invoke_help_command(ctx)

    @colour.command()
    async def rgb(self, ctx: commands.Context, red: int, green: int, blue: int) -> None:
        """Command to create an embed from an RGB input."""
        if any(c not in range(0, 256) for c in (red, green, blue)):
            raise BadArgument(
                message=f"RGB values can only be from 0 to 255. User input was: `{red, green, blue}`."
            )
        rgb_tuple = (red, green, blue)
        await self.send_colour_response(ctx, rgb_tuple)

    @colour.command()
    async def hsv(self, ctx: commands.Context, hue: int, saturation: int, value: int) -> None:
        """Command to create an embed from an HSV input."""
        if (hue not in range(0, 361)) or any(c not in range(0, 101) for c in (saturation, value)):
            raise BadArgument(
                message="Hue can only be from 0 to 360. Saturation and Value can only be from 0 to 100. "
                f"User input was: `{hue, saturation, value}`."
            )
        hsv_tuple = ImageColor.getrgb(f"hsv({hue}, {saturation}%, {value}%)")
        await self.send_colour_response(ctx, hsv_tuple)

    @colour.command()
    async def hsl(self, ctx: commands.Context, hue: int, saturation: int, lightness: int) -> None:
        """Command to create an embed from an HSL input."""
        if (hue not in range(0, 361)) or any(c not in range(0, 101) for c in (saturation, lightness)):
            raise BadArgument(
                message="Hue can only be from 0 to 360. Saturation and Lightness can only be from 0 to 100. "
                f"User input was: `{hue, saturation, lightness}`."
            )
        hsl_tuple = ImageColor.getrgb(f"hsl({hue}, {saturation}%, {lightness}%)")
        await self.send_colour_response(ctx, hsl_tuple)

    @colour.command()
    async def cmyk(self, ctx: commands.Context, cyan: int, magenta: int, yellow: int, key: int) -> None:
        """Command to create an embed from a CMYK input."""
        if any(c not in range(0, 101) for c in (cyan, magenta, yellow, key)):
            raise BadArgument(
                message=f"CMYK values can only be from 0 to 100. User input was: `{cyan, magenta, yellow, key}`."
            )
        r = round(255 * (1 - (cyan / 100)) * (1 - (key / 100)))
        g = round(255 * (1 - (magenta / 100)) * (1 - (key / 100)))
        b = round(255 * (1 - (yellow / 100)) * (1 - (key / 100)))
        await self.send_colour_response(ctx, (r, g, b))

    @colour.command()
    async def hex(self, ctx: commands.Context, hex_code: str) -> None:
        """Command to create an embed from a HEX input."""
        if "#" not in hex_code:
            hex_code = f"#{hex_code}"
        hex_tuple = ImageColor.getrgb(hex_code)
        await self.send_colour_response(ctx, hex_tuple)

    @colour.command()
    async def name(self, ctx: commands.Context, user_colour_name: str) -> None:
        """Command to create an embed from a name input."""
        hex_colour = self.match_colour_name(user_colour_name)
        hex_tuple = ImageColor.getrgb(hex_colour)
        await self.send_colour_response(ctx, hex_tuple)

    @colour.command()
    async def random(self, ctx: commands.Context) -> None:
        """Command to create an embed from a randomly chosen colour from the reference file."""
        hex_colour = random.choice(list(self.colour_mapping.values()))
        hex_tuple = ImageColor.getrgb(f"#{hex_colour}")
        await self.send_colour_response(ctx, hex_tuple)

    def get_colour_conversions(self, rgb: tuple[int, int, int]) -> dict[str, str]:
        """Create a dictionary mapping of colour types and their values."""
        return {
            "RGB": rgb,
            "HSV": self._rgb_to_hsv(rgb),
            "HSL": self._rgb_to_hsl(rgb),
            "CMYK": self._rgb_to_cmyk(rgb),
            "Hex": self._rgb_to_hex(rgb),
            "Name": self._rgb_to_name(rgb)
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
    def _rgb_to_cmyk(rgb: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        """Convert RGB values to CMYK values."""
        rgb_list = [val / 255.0 for val in rgb]
        if not any(rgb_list):
            return 0, 0, 0, 100
        k = 1 - max(val for val in rgb_list)
        c = round((1 - rgb_list[0] - k) * 100 / (1 - k))
        m = round((1 - rgb_list[1] - k) * 100 / (1 - k))
        y = round((1 - rgb_list[2] - k) * 100 / (1 - k))
        cmyk = (c, m, y, round(k * 100))
        return cmyk

    @staticmethod
    def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        """Convert RGB values to HEX code."""
        hex_ = ''.join([hex(val)[2:].zfill(2) for val in rgb])
        hex_code = f"#{hex_}".upper()
        return hex_code

    def _rgb_to_name(self, rgb: tuple[int, int, int]) -> str:
        """Convert RGB values to a fuzzy matched name."""
        input_hex_colour = self._rgb_to_hex(rgb)
        try:
            match, certainty, _ = process.extractOne(
                query=input_hex_colour,
                choices=self.colour_mapping.values(),
                score_cutoff=80
            )
            colour_name = [name for name, hex_code in self.colour_mapping.items() if hex_code == match][0]
        except TypeError:
            colour_name = "No match found"
        return colour_name

    def match_colour_name(self, input_colour_name: str) -> str:
        """Convert a colour name to HEX code."""
        try:
            match, certainty, _ = process.extractOne(
                query=input_colour_name,
                choices=self.colour_mapping.keys(),
                score_cutoff=80
            )
            hex_match = f"#{self.colour_mapping[match]}"
        except (ValueError, TypeError):
            raise BadArgument(message=f"No color found for: `{input_colour_name}`")
        return hex_match


def setup(bot: Bot) -> None:
    """Load the Colour cog."""
    bot.add_cog(Colour(bot))

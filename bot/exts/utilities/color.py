import colorsys
import json
import logging
import random
from io import BytesIO

from discord import Embed, File
from discord.ext import commands
from PIL import Image, ImageColor
from rapidfuzz import process

from bot.bot import Bot
from bot.exts.core.extensions import invoke_help_command

logger = logging.getLogger(__name__)


with open("bot/resources/utilities/ryanzec_colours.json") as f:
    COLOR_MAPPING = json.load(f)


THUMBNAIL_SIZE = 80


class Colour(commands.Cog):
    """Cog for the Colour command."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.group(aliases=["color"])
    async def colour(self, ctx: commands.Context) -> None:
        """
        User initiated command to create an embed that displays color information.

        For the commands `hsl`, `hsv` and `rgb`: input is in the form `.color <mode> <int> <int> <int>`
        For the command `cmyk`: input is in the form `.color cmyk <int> <int> <int> <int>`
        For the command `hex`: input is in the form `.color hex #<hex code>`
        For the command `name`: input is in the form `.color name <color name>`
        For the command `random`: input is in the form `.color random`
        """
        if ctx.invoked_subcommand is None:
            await invoke_help_command(ctx)

    @colour.command()
    async def rgb(self, ctx: commands.Context, red: int, green: int, blue: int) -> None:
        """Function to create an embed from an RGB input."""
        rgb_tuple = ImageColor.getrgb(f"rgb({red}, {green}, {blue})")
        await Colour.send_colour_response(ctx, list(rgb_tuple))

    @colour.command()
    async def hsv(self, ctx: commands.Context, hue: int, saturation: int, value: int) -> None:
        """Function to create an embed from an HSV input."""
        hsv_tuple = ImageColor.getrgb(f"hsv({hue}, {saturation}%, {value}%)")
        await Colour.send_colour_response(ctx, list(hsv_tuple))

    @colour.command()
    async def hsl(self, ctx: commands.Context, hue: int, saturation: int, lightness: int) -> None:
        """Function to create an embed from an HSL input."""
        hsl_tuple = ImageColor.getrgb(f"hsl({hue}, {saturation}%, {lightness}%)")
        await Colour.send_colour_response(ctx, list(hsl_tuple))

    @colour.command()
    async def cmyk(self, ctx: commands.Context, cyan: int, yellow: int, magenta: int, key: int) -> None:
        """Function to create an embed from a CMYK input."""
        r = int(255 * (1.0 - cyan / float(100)) * (1.0 - key / float(100)))
        g = int(255 * (1.0 - magenta / float(100)) * (1.0 - key / float(100)))
        b = int(255 * (1.0 - yellow / float(100)) * (1.0 - key / float(100)))
        await Colour.send_colour_response(ctx, list((r, g, b)))

    @colour.command()
    async def hex(self, ctx: commands.Context, hex_code: str) -> None:
        """Function to create an embed from a HEX input. (Requires # as a prefix)."""
        hex_tuple = ImageColor.getrgb(hex_code)
        await Colour.send_colour_response(ctx, list(hex_tuple))

    @colour.command()
    async def name(self, ctx: commands.Context, user_color: str) -> None:
        """Function to create an embed from a name input."""
        _, hex_color = self.match_color_name(user_color)
        hex_tuple = ImageColor.getrgb(hex_color)
        await Colour.send_colour_response(ctx, list(hex_tuple))

    @colour.command()
    async def random(self, ctx: commands.Context) -> None:
        """Function to create an embed from a randomly chosen color from the ryanzec.json file."""
        color_choices = list(COLOR_MAPPING.values())
        hex_color = random.choice(color_choices)
        hex_tuple = ImageColor.getrgb(f"#{hex_color}")
        await Colour.send_colour_response(ctx, list(hex_tuple))

    @staticmethod
    async def send_colour_response(ctx: commands.Context, rgb: list[int]) -> None:
        """Function to create and send embed from color information."""
        r, g, b = rgb[0], rgb[1], rgb[2]
        name = Colour._rgb_to_name(rgb)
        if name is None:
            desc = "Color information for the input color."
        else:
            desc = f"Color information for {name}"
        colour_embed = Embed(
            title="Colour",
            description=desc,
            colour=int(f"{r:02x}{g:02x}{b:02x}", 16)
        )
        colour_conversions = Colour.get_colour_conversions(rgb)
        for colour_space, value in colour_conversions.items():
            colour_embed.add_field(
                name=colour_space.upper(),
                value=f"`{value}`",
                inline=True
            )

        thumbnail = Image.new("RGB", (THUMBNAIL_SIZE, THUMBNAIL_SIZE), color=tuple(rgb))
        buffer = BytesIO()
        thumbnail.save(buffer, "PNG")
        buffer.seek(0)
        thumbnail_file = File(buffer, filename="colour.png")

        colour_embed.set_thumbnail(url="attachment://colour.png")

        await ctx.send(file=thumbnail_file, embed=colour_embed)

    @staticmethod
    def get_colour_conversions(rgb: list[int]) -> dict[str, str]:
        """Create a dictionary mapping of color types and their values."""
        return {
            "rgb": tuple(rgb),
            "hsv": Colour._rgb_to_hsv(rgb),
            "hsl": Colour._rgb_to_hsl(rgb),
            "cmyk": Colour._rgb_to_cmyk(rgb),
            "hex": Colour._rgb_to_hex(rgb),
            "name": Colour._rgb_to_name(rgb)
        }

    @staticmethod
    def _rgb_to_hsv(rgb: list[int]) -> tuple[int, int, int]:
        """Function to convert an RGB list to a HSV list."""
        rgb = [val / 255.0 for val in rgb]
        h, v, s = colorsys.rgb_to_hsv(*rgb)
        hsv = (round(h * 360), round(s * 100), round(v * 100))
        return hsv

    @staticmethod
    def _rgb_to_hsl(rgb: list[int]) -> tuple[int, int, int]:
        """Function to convert an RGB list to a HSL list."""
        rgb = [val / 255.0 for val in rgb]
        h, l, s = colorsys.rgb_to_hls(*rgb)
        hsl = (round(h * 360), round(s * 100), round(l * 100))
        return hsl

    @staticmethod
    def _rgb_to_cmyk(rgb: list[int]) -> tuple[int, int, int, int]:
        """Function to convert an RGB list to a CMYK list."""
        rgb = [val / 255.0 for val in rgb]
        if all(val == 0 for val in rgb):
            return 0, 0, 0, 100
        cmy = [1 - val / 255 for val in rgb]
        min_cmy = min(cmy)
        cmyk = [(val - min_cmy) / (1 - min_cmy) for val in cmy] + [min_cmy]
        cmyk = [round(val * 100) for val in cmyk]
        return tuple(cmyk)

    @staticmethod
    def _rgb_to_hex(rgb: list[int]) -> str:
        """Function to convert an RGB list to a HEX string."""
        hex_ = ''.join([hex(val)[2:].zfill(2) for val in rgb])
        hex_code = f"#{hex_}".upper()
        return hex_code

    @staticmethod
    def _rgb_to_name(rgb: list[int]) -> str:
        """Function to convert from an RGB list to a fuzzy matched color name."""
        input_hex_color = Colour._rgb_to_hex(rgb)
        try:
            match, certainty, _ = process.extractOne(
                query=input_hex_color,
                choices=COLOR_MAPPING.values(),
                score_cutoff=80
            )
            logger.debug(f"{match = }, {certainty = }")
            color_name = [name for name, _ in COLOR_MAPPING.items() if _ == match][0]
            logger.debug(f"{color_name = }")
        except TypeError:
            color_name = None
        return color_name

    @staticmethod
    def match_color_name(input_color_name: str) -> str:
        """Use fuzzy matching to return a hex color code based on the user's input."""
        try:
            match, certainty, _ = process.extractOne(
                query=input_color_name,
                choices=COLOR_MAPPING.keys(),
                score_cutoff=50
            )
            logger.debug(f"{match = }, {certainty = }")
            hex_match = f"#{COLOR_MAPPING[match]}"
            logger.debug(f"{hex_match = }")
        except TypeError:
            match = "No color name match found."
            hex_match = input_color_name
        return match, hex_match


def setup(bot: Bot) -> None:
    """Load the Colour cog."""
    bot.add_cog(Colour(bot))

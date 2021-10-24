import colorsys
import json
import logging
import re
from io import BytesIO

from discord import Embed, File
from discord.ext import commands
from PIL import Image, ImageColor
from rapidfuzz import process

from bot.bot import Bot
from bot.constants import Colours

# from bot.exts.core.extension import invoke_help_command


logger = logging.getLogger(__name__)


ERROR_MSG = """The color code {user_color} is not a possible color combination.
The range of possible values are:
RGB & HSV: 0-255
CMYK: 0-100%
HSL: 0-360 degrees
Hex: #000000-#FFFFFF
"""

with open("bot/resources/utilities/ryanzec_colours.json") as f:
    COLOR_MAPPING = json.load(f)


THUMBNAIL_SIZE = 80

"""
class Colour(commands.Cog):

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.group(aliases=["color"])
    async def colour(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await invoke_help_command(ctx)

    @colour.command()
    async def rgb(self, ctx: commands.Context, red: int, green: int, blue: int) -> None:
        rgb_tuple = ImageColor.getrgb(f"rgb({red}, {green}, {blue})")
        await Colour.send_colour_response(ctx, list(rgb_tuple))

    @colour.command()
    async def hsv(self, ctx: commands.Context, hue: int, saturation: int, value: int) -> None:
        hsv_tuple = ImageColor.getrgb(f"hsv({hue}, {saturation}%, {value}%)")
        await Colour.send_colour_response(ctx, list(hsv_tuple))

    @colour.command()
    async def hsl(self, ctx: commands.Context, hue: int, saturation: int, lightness: int) -> None:
        hsl_tuple = ImageColor.getrgb(f"hsl({hue}, {saturation}%, {lightness}%)")
        await Colour.send_colour_response(ctx, list(hsl_tuple))

    @colour.command()
    async def cmyk(self, ctx: commands.Context, cyan: int, yellow: int, magenta: int, key: int) -> None:
        ...

    @colour.command()
    async def hex(self, ctx: commands.Context, hex_code: str) -> None:
        hex_tuple = ImageColor.getrgb(hex_code)
        await Colour.send_colour_response(ctx, list(hex_tuple))

    @colour.command()
    async def yiq(
      self,
      ctx: commands.Context,
      perceived_luminesence: int,
      in_phase: int,
      quadrature: int
    ) -> None:
        yiq_list = list(colorsys.yiq_to_rgb(perceived_luminesence, in_phase, quadrature))
        yiq_tuple = [int(val * 255.0) for val in yiq_list]
        await Colour.send_colour_response(ctx, list(yiq_tuple))

    @staticmethod
    async def send_colour_response(ctx: commands.Context, rgb: list[int]) -> Message:
        r, g, b = rgb[0], rgb[1], rgb[2]
        colour_embed = Embed(
            title="Colour",
            description="Here lies thy colour",
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
        return {
            "rgb": tuple(rgb),
            "hsv": Colour._rgb_to_hsv(rgb),
            "hsl": Colour._rgb_to_hsl(rgb),
            "cmyk": Colour._rgb_to_cmyk(rgb),
            "hex": Colour._rgb_to_hex(rgb),
            "yiq": Colour._rgb_to_yiq(rgb)
        }

    @staticmethod
    def _rgb_to_hsv(rgb: list[int]) -> tuple[int, int, int]:
        rgb = [val / 255.0 for val in rgb]
        h, v, s = colorsys.rgb_to_hsv(*rgb)
        hsv = (round(h * 360), round(s * 100), round(v * 100))
        return hsv

    @staticmethod
    def _rgb_to_hsl(rgb: list[int]) -> tuple[int, int, int]:
        rgb = [val / 255.0 for val in rgb]
        h, l, s = colorsys.rgb_to_hls(*rgb)
        hsl = (round(h * 360), round(s * 100), round(l * 100))
        return hsl

    @staticmethod
    def _rgb_to_cmyk(rgb: list[int]) -> tuple[int, int, int, int]:
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
        hex_ = ''.join([hex(val)[2:].zfill(2) for val in rgb])
        hex_code = f"#{hex_}".upper()
        return hex_code

    @staticmethod
    def _rgb_to_yiq(rgb: list[int]) -> tuple[int, int, int, int]:
        rgb = [val / 255.0 for val in rgb]
        y, i, q = colorsys.rgb_to_yiq(*rgb)
        yiq = (round(y), round(i), round(q))
        return yiq

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Colour(bot))
"""


class Color(commands.Cog):
    """User initiated commands to receive color information."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(aliases=["colour"])
    async def color(self, ctx: commands.Context, mode: str, *, user_color: str) -> None:
        """
        Send information on input color code or color name.

        Possible modes are: "hex", "rgb", "hsv", "hsl", "cmyk" or "name".
        """
        logger.debug(f"{mode = }")
        logger.debug(f"{user_color = }")
        if mode.lower() == "hex":
            await self.hex_to_rgb(ctx, user_color)
        elif mode.lower() == "rgb":
            rgb_color = self.tuple_create(user_color)
            await self.color_embed(ctx, rgb_color)
        elif mode.lower() == "hsv":
            await self.hsv_to_rgb(ctx, user_color)
        elif mode.lower() == "hsl":
            await self.hsl_to_rgb(ctx, user_color)
        elif mode.lower() == "cmyk":
            await self.cmyk_to_rgb(ctx, user_color)
        elif mode.lower() == "name":
            color_name, hex_color = self.match_color_name(user_color)
            if "#" in hex_color:
                rgb_color = ImageColor.getcolor(hex_color, "RGB")
            else:
                rgb_color = ImageColor.getcolor("#" + hex_color, "RGB")
            await self.color_embed(ctx, rgb_color, color_name)
        else:
            # mode is either None or an invalid code
            if mode is None:
                no_mode_embed = Embed(
                    title="No mode was passed, please define a color code.",
                    description="Possible modes are: Name, Hex, RGB, HSV, HSL and CMYK.",
                    color=Colours.soft_red,
                )
                await ctx.send(embed=no_mode_embed)
                return
            wrong_mode_embed = Embed(
                title=f"The color code {mode} is not a valid option",
                description="Possible modes are: Name, Hex, RGB, HSV, HSL and CMYK.",
                color=Colours.soft_red,
            )
            await ctx.send(embed=wrong_mode_embed)
            return

    @staticmethod
    def tuple_create(input_color: str) -> tuple[int, int, int]:
        """
        Create a tuple of integers based on user's input.

        Can handle inputs of the types:
        (100, 100, 100)
        100, 100, 100
        100 100 100
        """
        if "(" in input_color:
            remove = "[() ]"
            color_tuple = re.sub(remove, "", input_color)
            color_tuple = tuple(map(int, color_tuple.split(",")))
        elif "," in input_color:
            color_tuple = tuple(map(int, input_color.split(",")))
        else:
            color_tuple = tuple(map(int, input_color.split(" ")))
        return color_tuple

    async def hex_to_rgb(self, ctx: commands.Context, hex_string: str) -> None:
        """Function to convert hex color to rgb color and send main embed."""
        hex_match = re.fullmatch(r"(#?[0x]?)((?:[0-9a-fA-F]{3}){1,2})", hex_string)
        if hex_match:
            if "#" in hex_string:
                rgb_color = ImageColor.getcolor(hex_string, "RGB")
            elif "0x" in hex_string:
                hex_ = hex_string.replace("0x", "#")
                rgb_color = ImageColor.getcolor(hex_, "RGB")
            else:
                hex_ = "#" + hex_string
                rgb_color = ImageColor.getcolor(hex_, "RGB")
            await self.color_embed(ctx, rgb_color)
        else:
            await ctx.send(
                embed=Embed(
                    title="There was an issue converting the hex color code.",
                    description=ERROR_MSG.format(user_color=hex_string),
                )
            )

    async def hsv_to_rgb(self, ctx: commands.Context, input_color: tuple[int, int, int]) -> tuple[int, int, int]:
        """Function to convert hsv color to rgb color and send main embed."""
        input_color = self.tuple_create(input_color)
        (h, v, s) = input_color  # the function hsv_to_rgb expects v and s to be swapped
        h = h / 360
        s = s / 100
        v = v / 100
        rgb_color = colorsys.hsv_to_rgb(h, s, v)
        (r, g, b) = rgb_color
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        await self.color_embed(ctx, (r, g, b))

    async def hsl_to_rgb(self, ctx: commands.Context, input_color: tuple[int, int, int]) -> tuple[int, int, int]:
        """Function to convert hsl color to rgb color and send main embed."""
        input_color = self.tuple_create(input_color)
        (h, s, l) = input_color
        h = h / 360
        s = s / 100
        l = l / 100  # noqa: E741 It's little `L`, Reason: To maintain consistency.
        rgb_color = colorsys.hls_to_rgb(h, l, s)
        (r, g, b) = rgb_color
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        await self.color_embed(ctx, (r, g, b))

    async def cmyk_to_rgb(
        self,
        ctx: commands.Context,
        input_color: tuple[int, int, int, int]
    ) -> tuple[int, int, int]:
        """Function to convert cmyk color to rgb color and send main embed."""
        input_color = self.tuple_create(input_color)
        c = input_color[0]
        m = input_color[1]
        y = input_color[2]
        k = input_color[3]
        r = int(255 * (1.0 - c / float(100)) * (1.0 - k / float(100)))
        g = int(255 * (1.0 - m / float(100)) * (1.0 - k / float(100)))
        b = int(255 * (1.0 - y / float(100)) * (1.0 - k / float(100)))
        await self.color_embed(ctx, (r, g, b))

    @staticmethod
    async def create_thumbnail_attachment(color: tuple[int, int, int]) -> File:
        """
        Generate a thumbnail from `color`.

        Assumes that color is an rgb tuple.
        """
        thumbnail = Image.new("RGB", (80, 80), color=color)
        bufferedio = BytesIO()
        thumbnail.save(bufferedio, format="PNG")
        bufferedio.seek(0)

        file = File(bufferedio, filename="color.png")

        return file

    @staticmethod
    def get_color_fields(rgb_color: tuple[int, int, int]) -> list[dict]:
        """Converts from `RGB` to `CMYK`, `HSV`, `HSL` and returns a list of fields."""

        def _rgb_to_hex(rgb_color: tuple[int, int, int]) -> str:
            """To convert from `RGB` to `Hex` notation."""
            return '#' + ''.join(hex(int(color))[2:].zfill(2) for color in rgb_color).upper()

        def _rgb_to_cmyk(rgb_color: tuple[int, int, int]) -> tuple[int, int, int, int]:
            """To convert from `RGB` to `CMYK` color space."""
            r, g, b = rgb_color

            # RGB_SCALE -> 255
            # CMYK_SCALE -> 100

            if (r == g == b == 0):
                return 0, 0, 0, 100  # Representing Black

            # rgb [0,RGB_SCALE] -> cmy [0,1]
            c = 1 - r / 255
            m = 1 - g / 255
            y = 1 - b / 255

            # extract out k [0, 1]
            min_cmy = min(c, m, y)
            c = (c - min_cmy) / (1 - min_cmy)
            m = (m - min_cmy) / (1 - min_cmy)
            y = (y - min_cmy) / (1 - min_cmy)
            k = min_cmy

            # rescale to the range [0,CMYK_SCALE] and round off
            c = round(c * 100)
            m = round(m * 100)
            y = round(y * 100)
            k = round(k * 100)

            return c, m, y, k

        def _rgb_to_hsv(rgb_color: tuple[int, int, int]) -> tuple[int, int, int]:
            """To convert from `RGB` to `HSV` color space."""
            r, g, b = rgb_color
            h, v, s = colorsys.rgb_to_hsv(r / float(255), g / float(255), b / float(255))
            h = round(h * 360)
            s = round(s * 100)
            v = round(v * 100)
            return h, s, v

        def _rgb_to_hsl(rgb_color: tuple[int, int, int]) -> tuple[int, int, int]:
            """To convert from `RGB` to `HSL` color space."""
            r, g, b = rgb_color
            h, l, s = colorsys.rgb_to_hls(r / float(255), g / float(255), b / float(255))
            h = round(h * 360)
            s = round(s * 100)
            l = round(l * 100)  # noqa: E741 It's little `L`, Reason: To maintain consistency.
            return h, s, l

        all_fields = [
            {
                "name": "RGB",
                "value": f"» rgb {rgb_color}"
            },
            {
                "name": "HEX",
                "value": f"» hex {_rgb_to_hex(rgb_color)}"
            },
            {
                "name": "CMYK",
                "value": f"» cmyk {_rgb_to_cmyk(rgb_color)}"
            },
            {
                "name": "HSV",
                "value": f"» hsv {_rgb_to_hsv(rgb_color)}"
            },
            {
                "name": "HSL",
                "value": f"» hsl {_rgb_to_hsl(rgb_color)}"
            },
        ]

        return all_fields

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
            hex_match = COLOR_MAPPING[match]
            logger.debug(f"{hex_match = }")
        except TypeError:
            match = "No color name match found."
            hex_match = input_color_name

        return match, hex_match

    @staticmethod
    def match_color_hex(input_hex_color: str) -> str:
        """Use fuzzy matching to return a hex color code based on the user's input."""
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
            color_name = "No color name match found."

        return color_name

    async def color_embed(
        self,
        ctx: commands.Context,
        rgb_color: tuple[int, int, int],
        color_name: str = None
    ) -> None:
        """Take a RGB color tuple, create embed, and send."""
        (r, g, b) = rgb_color
        discord_rgb_int = int(f"{r:02x}{g:02x}{b:02x}", 16)
        all_colors = self.get_color_fields(rgb_color)
        hex_color = all_colors[1]["value"].replace("» hex ", "")
        if color_name is None:
            logger.debug(f"Find color name from hex color: {hex_color}")
            color_name = self.match_color_hex(hex_color)

        async with ctx.typing():
            main_embed = Embed(
                title=color_name,
                description='(Approx..)',
                color=discord_rgb_int,
            )

            file = await self.create_thumbnail_attachment(rgb_color)
            main_embed.set_thumbnail(url="attachment://color.png")

            for field in all_colors:
                main_embed.add_field(
                    name=field['name'],
                    value=field['value'],
                    inline=False,
                )

            await ctx.send(file=file, embed=main_embed)


def setup(bot: Bot) -> None:
    """Load the Color Cog."""
    bot.add_cog(Color(bot))

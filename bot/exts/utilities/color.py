import colorsys
import json
import logging
import re
from io import BytesIO

from PIL import Image, ImageColor
from discord import Embed, File
from discord.ext import commands
from rapidfuzz import process

from bot.bot import Bot
from bot.constants import Colours


logger = logging.getLogger(__name__)


ERROR_MSG = """The color code {user_color} is not a possible color combination.
\nThe range of possible values are:
\nRGB & HSV: 0-255
\nCMYK: 0-100%
\nHSL: 0-360 degrees
\nHex: #000000-#FFFFFF
"""

COLOR_JSON_PATH = "bot/resources/utilities/ryanzec_colours.json"
with open(COLOR_JSON_PATH) as f:
    COLOR_MAPPING = json.load(f)


# define color command
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
        color_name = None
        if mode.lower() == "hex":
            hex_match = re.fullmatch(r"(#?[0x]?)((?:[0-9a-fA-F]{3}){1,2})", user_color)
            if hex_match:
                hex_color = int(hex(int(user_color.replace("#", ""), 16)), 0)
                if "#" in user_color:
                    rgb_color = ImageColor.getcolor(user_color, "RGB")
                elif "0x" in user_color:
                    hex_ = user_color.replace("0x", "#")
                    rgb_color = ImageColor.getcolor(hex_, "RGB")
                else:
                    hex_ = "#" + user_color
                    rgb_color = ImageColor.getcolor(hex_, "RGB")
            else:
                await ctx.send(
                    embed=Embed(
                        title="There was an issue converting the hex color code.",
                        description=ERROR_MSG.format(user_color=user_color),
                    )
                )
        elif mode.lower() == "rgb":
            rgb_color = self.tuple_create(user_color)
        elif mode.lower() == "hsv":
            hsv_temp = self.tuple_create(user_color)
            rgb_color = self.hsv_to_rgb(hsv_temp)
        elif mode.lower() == "hsl":
            hsl_temp = self.tuple_create(user_color)
            rgb_color = self.hsl_to_rgb(hsl_temp)
        elif mode.lower() == "cmyk":
            cmyk_temp = self.tuple_create(user_color)
            rgb_color = self.cmyk_to_rgb(cmyk_temp)
        elif mode.lower() == "name":
            color_name, hex_color = self.match_color_name(user_color)
            if "#" in hex_color:
                rgb_color = ImageColor.getcolor(hex_color, "RGB")
            else:
                rgb_color = ImageColor.getcolor("#" + hex_color, "RGB")
        else:
            # mode is either None or an invalid code
            if mode is None:
                no_mode_embed = Embed(
                    title="No 'mode' was passed, please define a color code.",
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
            fields = self.get_color_fields(rgb_color)

            for field in fields:
                main_embed.add_field(
                    name=field['name'],
                    value=field['value'],
                    inline=False,
                )

            await ctx.send(file=file, embed=main_embed)

    @staticmethod
    async def create_thumbnail_attachment(color: str) -> File:
        """Generate a thumbnail from `color`."""
        thumbnail = Image.new("RGB", (100, 100), color=color)
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

        hex_color = _rgb_to_hex(rgb_color)
        cmyk_color = _rgb_to_cmyk(rgb_color)
        hsv_color = _rgb_to_hsv(rgb_color)
        hsl_color = _rgb_to_hsl(rgb_color)

        all_fields = [
            {
                "name": "RGB",
                "value": f"» rgb {rgb_color}"
            },
            {
                "name": "HEX",
                "value": f"» hex {hex_color}"
            },
            {
                "name": "CMYK",
                "value": f"» cmyk {cmyk_color}"
            },
            {
                "name": "HSV",
                "value": f"» hsv {hsv_color}"
            },
            {
                "name": "HSL",
                "value": f"» hsl {hsl_color}"
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
            return match, hex_match
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
            return color_name
        except TypeError:
            color_name = "No color name match found."
            return color_name

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

    @staticmethod
    def hsv_to_rgb(input_color: tuple[int, int, int]) -> tuple[int, int, int]:
        """Function to convert hsv color to rgb color."""
        (h, v, s) = input_color  # the function hsv_to_rgb expects v and s to be swapped
        h = h / 360
        s = s / 100
        v = v / 100
        rgb_color = colorsys.hsv_to_rgb(h, s, v)
        (r, g, b) = rgb_color
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        return r, g, b

    @staticmethod
    def hsl_to_rgb(input_color: tuple[int, int, int]) -> tuple[int, int, int]:
        """Function to convert hsl color to rgb color."""
        (h, s, l) = input_color
        h = h / 360
        s = s / 100
        l = l / 100  # noqa: E741 It's little `L`, Reason: To maintain consistency.
        rgb_color = colorsys.hls_to_rgb(h, l, s)
        (r, g, b) = rgb_color
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        return r, g, b

    @staticmethod
    def cmyk_to_rgb(input_color: tuple[int, int, int, int]) -> tuple[int, int, int]:
        """Function to convert cmyk color to rgb color."""
        c = input_color[0]
        m = input_color[1]
        y = input_color[2]
        k = input_color[3]
        r = int(255 * (1.0 - c / float(100)) * (1.0 - k / float(100)))
        g = int(255 * (1.0 - m / float(100)) * (1.0 - k / float(100)))
        b = int(255 * (1.0 - y / float(100)) * (1.0 - k / float(100)))
        return r, g, b


def setup(bot: Bot) -> None:
    """Load the Color Cog."""
    bot.add_cog(Color(bot))

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

COLOR_LIST = "bot/resources/utilities/ryanzec_colours.json"


# define color command
class Color(commands.Cog):
    """User initiated command to receive color information."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(aliases=["colour"])
    async def color(self, ctx: commands.Context, mode: str, *, user_color: str) -> None:
        """Send information on input color code or color name."""
        logger.info(f"{mode = }")
        logger.info(f"{user_color = }")
        if mode.lower() == "hex":
            hex_match = re.search(r"^#(?:[0-9a-fA-F]{3}){1,2}$", user_color)
            if hex_match:
                hex_color = int(hex(int(user_color.replace("#", ""), 16)), 0)
                rgb_color = ImageColor.getcolor(user_color, "RGB")
                logger.info(f"{hex_color = }")
                logger.info(f"{rgb_color = }")
            else:
                await ctx.send(
                    embed=Embed(
                        title="There was an issue converting the hex color code.",
                        description=ERROR_MSG.format(user_color=user_color),
                    )
                )
        elif mode.lower() == "rgb":
            pass
        elif mode.lower() == "hsv":
            pass
        elif mode.lower() == "hsl":
            pass
        elif mode.lower() == "cmyk":
            pass
        elif mode.lower() == "name":
            color_name, hex_color = self.match_color(user_color)
        else:
            # mode is either None or an invalid code
            if mode is None:
                no_mode_embed = Embed(
                    title="No 'mode' was passed, please define a color code.",
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

        async with ctx.typing():
            main_embed = Embed(
                title=color_name,
                description='(Approx..)',
                color=rgb_color,
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
            return '#' + ''.join(hex(color)[2:].zfill(2) for color in rgb_color).upper()

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
            h, v, s = colorsys.rgb_to_hsv(r/float(255), g/float(255), b/float(255))
            h = round(h*360)
            s = round(s*100)
            v = round(v*100)
            return h, s, v

        def _rgb_to_hsl(rgb_color: tuple[int, int, int]) -> tuple[int, int, int]:
            """To convert from `RGB` to `HSL` color space."""
            r, g, b = rgb_color
            h, l, s = colorsys.rgb_to_hls(r/float(255), g/float(255), b/float(255))
            h = round(h*360)
            s = round(s*100)
            l = round(l*100)  # noqa: E741 It's little `L`, Reason: To maintain consistency.
            return h, s, l

        hex_color = _rgb_to_hex(rgb_color)
        cmyk_color = _rgb_to_cmyk(rgb_color)
        hsv_color = _rgb_to_hsv(rgb_color)
        hsl_color = _rgb_to_hsl(rgb_color)

        all_fields = [
            {
                "name": "RGB",
                "value": f"» rgb {rgb_color}\n» hex {hex_color}"
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

    # if user_color in color_lists:
    #     # fuzzy match for color
    @staticmethod
    def match_color(user_color: str) -> str:
        """Use fuzzy matching to return a hex color code based on the user's input."""
        with open(COLOR_LIST) as f:
            color_list = json.load(f)
        logger.debug(f"{type(color_list) = }")
        match, certainty, _ = process.extractOne(query=user_color, choices=color_list.keys(), score_cutoff=50)
        logger.debug(f"{match = }, {certainty = }")
        hex_match = color_list[match]
        logger.debug(f"{hex_match = }")
        return match, hex_match


def setup(bot: Bot) -> None:
    """Load the Color Cog."""
    bot.add_cog(Color(bot))

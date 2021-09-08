# import colorsys
import logging
import re
from io import BytesIO

from PIL import Image, ImageColor
from discord import Embed, File
from discord.ext import commands
# from rapidfuzz import process

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


# define color command
class Color(commands.Cog):
    """User initiated command to receive color information."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(aliases=["colour"])
    async def color(self, ctx: commands.Context, mode: str, user_color: str) -> None:
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
                        title="An error has occured.",
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
        else:
            # mode is either None or an invalid code
            # need to handle whether user passes color name
            if mode is None:
                no_mode_embed = Embed(
                    title="No 'mode' was passed, please define a color code.",
                    color=Colours.soft_red,
                )
                await ctx.send(embed=no_mode_embed)
                return
            wrong_mode_embed = Embed(
                title=f"The color code {mode} is not a valid option",
                description="Possible modes are: Hex, RGB, HSV, HSL and CMYK.",
                color=Colours.soft_red,
            )
            await ctx.send(embed=wrong_mode_embed)
            return

        main_embed = Embed(
            title=user_color,  # need to replace with fuzzymatch color name
            color=hex_color,
        )
        async with ctx.typing():
            file = await self._create_thumbnail_attachment(rgb_color)
            main_embed.set_thumbnail(url="attachment://color.png")

        main_embed.add_field(
            name="Hex",
            value=f">>Hex #{hex_color}",
            inline=False,
        )
        main_embed.add_field(
            name="RGB",
            value=f">>RGB {rgb_color}",
            inline=False,
        )
        """
        main_embed.add_field(
            name="HSV",
            value=f">>HSV {hsv_color}",
            inline=False,
        )
        main_embed.add_field(
            name="HSL",
            value=f">>HSL {hsl_color}",
            inline=False,
        )
        main_embed.add_field(
            name="CMYK",
            value=f">>CMYK {cmyk_color}",
            inline=False,
        )
        """
        await ctx.send(file=file, embed=main_embed)

    async def _create_thumbnail_attachment(self, color: str) -> File:
        """Generate a thumbnail from `color`."""
        thumbnail = Image.new("RGB", (100, 100), color=color)
        bufferedio = BytesIO()
        thumbnail.save(bufferedio, format="PNG")
        bufferedio.seek(0)

        file = File(bufferedio, filename="color.png")

        return file

    # if user_color in color_lists:
    #     # fuzzy match for color


def setup(bot: Bot) -> None:
    """Load the Color Cog."""
    bot.add_cog(Color(bot))

# imports
# import colorsys
import logging
import re
from io import BytesIO

from PIL import Image, ImageColor
from discord import Embed, File
from discord.ext import commands
# from rapidfuzz import process

from bot.bot import Bot
# from bot.constants import Colours


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
    @commands.cooldown(1, 10, commands.cooldowns.BucketType.user)
    async def color(self, ctx: commands.Context, *, user_color: str) -> None:
        """Send information on input color code or color name."""
        # need to check if user_color is RGB, HSV, CMYK, HSL, Hex or color name
        # should we assume the color is RGB if not defined?

        if "#" in user_color:
            logger.info(f"{user_color = }")
            hex_match = re.search(r"^#(?:[0-9a-fA-F]{3}){1,2}$", user_color)
            if hex_match:
                hex_color = int(hex(int(user_color.replace("#", ""), 16)), 0)
                logger.info(f"{hex_color = }")
                rgb_color = ImageColor.getcolor(user_color, "RGB")
                logger.info(f"{rgb_color = }")
            else:
                await ctx.send(
                    embed=Embed(
                        title="An error has occured.",
                        description=ERROR_MSG.format(user_color=user_color),
                    )
                )

        elif "RGB" or "rgb" in user_color:
            rgb_parse = user_color.split()
            rgb = rgb_parse[1:].replace(", ", "")
            logger.info(f"{rgb = }")
            logger.info(f"{rgb[0] = }")
            logger.info(f"{rgb[1] = }")
            logger.info(f"{rgb[2] = }")
            rgb_color = tuple(rgb)
            hex_color = f"0x{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}"

        main_embed = Embed(
            title=user_color,  # need to replace with fuzzymatch color name
            color=hex_color,
        )
        async with ctx.typing():
            file = await self._create_thumbnail_attachment(rgb_color)
            main_embed.set_thumbnail(url="attachment://color.png")

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

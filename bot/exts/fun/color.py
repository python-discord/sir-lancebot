# imports
import logging

import pillow
from discord import Embed
# ! need to install discord-flags and add to poetry.lock file
from discord.ext import commands, flags
from rapidfuzz import process

from bot.bot import Bot
from bot.constants import Colours

logger = logging.getLogger(__name__)

# constants if needed
# TODO Will the color conversions be done only from pillow or will an API / URL be needed?
# Color URLs
COLOR_URL_XKCD = "https://xkcd.com/color/rgb/"
COLOR_URL_NAME_THAT_COLOR = "https://github.com/ryanzec/name-that-color/blob/master/lib/ntc.js#L116-L1681"


COLOR_ERROR = Embed(
    title="Input color is not possible",
    description="The color code {user_color} is not a possible color combination."
    "\nThe range of possible values are: "
    "\nRGB & HSV: 0-255"
    "\nCMYK: 0-100%"
    "\nHSL: 0-360 degrees"
    "\nHex: #000000-#FFFFFF"
)
COLOR_EMBED = Embed(
    title="{color_name}",
    description="RGB"
    "\n{RGB}"
    "\nHSV"
    "\n{HSV}"
    "\nCMYK"
    "\n{CMYK}"
    "\nHSL"
    "\n{HSL}"
    "\nHex"
    "\n{Hex}"
)


# define color command
class Color(commands.cog):
    """User initiated command to receive color information."""

    def __init__(self, bot: Bot):
        self.bot = bot

    # ? possible to use discord-flags to allow user to decide on color
    # https://pypi.org/project/discord-flags/
    # @flags.add_flag("--rgb", type=str)
    # @flags.add_flag("--hsv", type=str)
    # @flags.add_flag("--cmyk", type=str)
    # @flags.add_flag("--hsl", type=str)
    # @flags.add_flag("--hex", type=str)
    # @flags.add_flag("--name", type=str)
    # @flags.command()
    @commands.command(aliases=["color", "colour"])
    @commands.cooldown(1, 10, commands.cooldowns.BucketType.user)
    async def color(self, ctx: commands.Context, *, user_color: str) -> None:
        """Send information on input color code or color name."""
        # need to check if user_color is RGB, HSV, CMYK, HSL, Hex or color name
        # should we assume the color is RGB if not defined?
        # should discord tags be used?
        # need to review discord.py V2.0

        # TODO code to check if color code is possible
        await ctx.send(embed=COLOR_ERROR.format(color=user_color))
        # await ctx.send(embed=COLOR_EMBED.format(
        #     RGB=color_dict["RGB"],
        #     HSV=color_dict["HSV"],
        #     HSL=color_dict["HSL"],
        #     CMYK=color_dict["CMYK"],
        #     HSL=color_dict["HSL"],
        #     Hex=color_dict["Hex"],
        #     color_name=color_dict["color_name"]
        #     )
        # )

        # TODO pass for now
        pass

    # if user_color in color_lists:
    #     # TODO fuzzy match for color
    #     pass

    async def color_converter(self, color: str, code_type: str) -> dict:
        """Generate alternative color codes for use in the embed."""
        # TODO add code to take color and code type and return other types
        # color_dict = {
        #     "RGB": color_RGB,
        #     "HSV": color_HSV,
        #     "HSL": color_HSL,
        #     "CMYK": color_CMYK,
        #     "HSL": color_HSL,
        #     "Hex": color_Hex,
        #     "color_name": color_name,
        # }
        pass

    async def photo_generator(self, color: str) -> None:
        """Generate photo to use in embed."""
        # TODO need to find a way to store photo in cache to add to embed, then remove


def setup(bot: Bot) -> None:
    """Load the Color Cog."""
    bot.add_cog(Color(bot))

import colorsys
import json
import pathlib
import random
from io import BytesIO

from PIL import Image, ImageColor
from discord import Embed, File
from discord.ext import commands
from rapidfuzz import process

from bot.bot import Bot
from bot.exts.core.extensions import invoke_help_command

THUMBNAIL_SIZE = (80, 80)


class Colour(commands.Cog):
    """Cog for the Colour command."""

    def __init__(self, bot: Bot):
        self.bot = bot
        with open(pathlib.Path("bot/resources/utilities/ryanzec_colours.json")) as f:
            self.COLOUR_MAPPING = json.load(f)

    @commands.group(aliases=("color",))
    async def colour(self, ctx: commands.Context) -> None:
        """User initiated command to create an embed that displays colour information."""
        if ctx.invoked_subcommand is None:
            await invoke_help_command(ctx)

    @colour.command()
    async def rgb(self, ctx: commands.Context, red: int, green: int, blue: int) -> None:
        """
        Command to create an embed from an RGB input.

        Input is in the form `.colour rgb <int> <int> <int>`
        """
        rgb_tuple = ImageColor.getrgb(f"rgb({red}, {green}, {blue})")
        await self.send_colour_response(ctx, list(rgb_tuple))

    @colour.command()
    async def hsv(self, ctx: commands.Context, hue: int, saturation: int, value: int) -> None:
        """
        Command to create an embed from an HSV input.

        Input is in the form `.colour hsv <int> <int> <int>`
        """
        hsv_tuple = ImageColor.getrgb(f"hsv({hue}, {saturation}%, {value}%)")
        await self.send_colour_response(ctx, list(hsv_tuple))

    @colour.command()
    async def hsl(self, ctx: commands.Context, hue: int, saturation: int, lightness: int) -> None:
        """
        Command to create an embed from an HSL input.

        Input is in the form `.colour hsl <int> <int> <int>`
        """
        hsl_tuple = ImageColor.getrgb(f"hsl({hue}, {saturation}%, {lightness}%)")
        await self.send_colour_response(ctx, list(hsl_tuple))

    @colour.command()
    async def cmyk(self, ctx: commands.Context, cyan: int, yellow: int, magenta: int, key: int) -> None:
        """
        Command to create an embed from a CMYK input.

        Input is in the form `.colour cmyk <int> <int> <int> <int>`
        """
        r = int(255 * (1.0 - cyan / float(100)) * (1.0 - key / float(100)))
        g = int(255 * (1.0 - magenta / float(100)) * (1.0 - key / float(100)))
        b = int(255 * (1.0 - yellow / float(100)) * (1.0 - key / float(100)))
        await self.send_colour_response(ctx, list((r, g, b)))

    @colour.command()
    async def hex(self, ctx: commands.Context, hex_code: str) -> None:
        """
        Command to create an embed from a HEX input.

        Input is in the form `.colour hex #<hex code>`
        """
        hex_tuple = ImageColor.getrgb(hex_code)
        await self.send_colour_response(ctx, list(hex_tuple))

    @colour.command()
    async def name(self, ctx: commands.Context, user_colour: str) -> None:
        """
        Command to create an embed from a name input.

        Input is in the form `.colour name <color name>`
        """
        _, hex_colour = self.match_colour_name(user_colour)
        hex_tuple = ImageColor.getrgb(hex_colour)
        await self.send_colour_response(ctx, list(hex_tuple))

    @colour.command()
    async def random(self, ctx: commands.Context) -> None:
        """
        Command to create an embed from a randomly chosen colour from the reference file.

        Input is in the form `.colour random`
        """
        colour_choices = list(self.COLOUR_MAPPING.values())
        hex_colour = random.choice(colour_choices)
        hex_tuple = ImageColor.getrgb(f"#{hex_colour}")
        await self.send_colour_response(ctx, list(hex_tuple))

    async def send_colour_response(self, ctx: commands.Context, rgb: list[int]) -> None:
        """Function to create and send embed from colour information."""
        r, g, b = rgb[0], rgb[1], rgb[2]
        name = self._rgb_to_name(rgb)
        colour_mode = ctx.invoked_with
        if name is None:
            desc = f"{colour_mode.upper()} information for the input colour."
        else:
            desc = f"{colour_mode.upper()} information for `{name}`."
        colour_embed = Embed(
            title="Colour",
            description=desc,
            colour=int(f"{r:02x}{g:02x}{b:02x}", 16)
        )
        colour_conversions = self.get_colour_conversions(rgb)
        for colour_space, value in colour_conversions.items():
            colour_embed.add_field(
                name=colour_space.upper(),
                value=f"`{value}`",
                inline=True
            )

        thumbnail = Image.new("RGB", THUMBNAIL_SIZE, color=tuple(rgb))
        buffer = BytesIO()
        thumbnail.save(buffer, "PNG")
        buffer.seek(0)
        thumbnail_file = File(buffer, filename="colour.png")

        colour_embed.set_thumbnail(url="attachment://colour.png")

        await ctx.send(file=thumbnail_file, embed=colour_embed)

    def get_colour_conversions(self, rgb: list[int]) -> dict[str, str]:
        """Create a dictionary mapping of colour types and their values."""
        return {
            "rgb": tuple(rgb),
            "hsv": self._rgb_to_hsv(rgb),
            "hsl": self._rgb_to_hsl(rgb),
            "cmyk": self._rgb_to_cmyk(rgb),
            "hex": self._rgb_to_hex(rgb),
            "name": self._rgb_to_name(rgb)
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

    def _rgb_to_name(self, rgb: list[int]) -> str:
        """Function to convert from an RGB list to a fuzzy matched colour name."""
        input_hex_colour = self._rgb_to_hex(rgb)
        try:
            match, certainty, _ = process.extractOne(
                query=input_hex_colour,
                choices=self.COLOUR_MAPPING.values(),
                score_cutoff=80
            )
            colour_name = [name for name, _ in self.COLOUR_MAPPING.items() if _ == match][0]
        except TypeError:
            colour_name = None
        return colour_name

    def match_colour_name(self, input_colour_name: str) -> str:
        """Use fuzzy matching to return a hex colour code based on the user's input."""
        try:
            match, certainty, _ = process.extractOne(
                query=input_colour_name,
                choices=self.COLOUR_MAPPING.keys(),
                score_cutoff=50
            )
            hex_match = f"#{self.COLOUR_MAPPING[match]}"
        except TypeError:
            match = "No colour name match found."
            hex_match = input_colour_name
        return match, hex_match


def setup(bot: Bot) -> None:
    """Load the Colour cog."""
    bot.add_cog(Colour(bot))

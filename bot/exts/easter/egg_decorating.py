import json
import logging
import random
from contextlib import suppress
from io import BytesIO
from pathlib import Path
from typing import Union

import discord
from PIL import Image
from discord.ext import commands

log = logging.getLogger(__name__)

with open(Path("bot/resources/evergreen/html_colours.json")) as f:
    HTML_COLOURS = json.load(f)

with open(Path("bot/resources/evergreen/xkcd_colours.json")) as f:
    XKCD_COLOURS = json.load(f)

COLOURS = [
    (255, 0, 0, 255), (255, 128, 0, 255), (255, 255, 0, 255), (0, 255, 0, 255),
    (0, 255, 255, 255), (0, 0, 255, 255), (255, 0, 255, 255), (128, 0, 128, 255)
]  # Colours to be replaced - Red, Orange, Yellow, Green, Light Blue, Dark Blue, Pink, Purple

IRREPLACEABLE = [
    (0, 0, 0, 0), (0, 0, 0, 255)
]  # Colours that are meant to stay the same - Transparent and Black


class EggDecorating(commands.Cog):
    """Decorate some easter eggs!"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def replace_invalid(colour: str) -> Union[int, None]:
        """Attempts to match with HTML or XKCD colour names, returning the int value."""
        with suppress(KeyError):
            return int(HTML_COLOURS[colour], 16)
        with suppress(KeyError):
            return int(XKCD_COLOURS[colour], 16)
        return None

    @commands.command(aliases=["decorateegg"])
    async def eggdecorate(
        self, ctx: commands.Context, *colours: Union[discord.Colour, str]
    ) -> Union[Image.Image, discord.Message]:
        """
        Picks a random egg design and decorates it using the given colours.

        Colours are split by spaces, unless you wrap the colour name in double quotes.
        Discord colour names, HTML colour names, XKCD colour names and hex values are accepted.
        """
        if len(colours) < 2:
            return await ctx.send("You must include at least 2 colours!")

        invalid = []
        colours = list(colours)
        for idx, colour in enumerate(colours):
            if isinstance(colour, discord.Colour):
                continue
            value = self.replace_invalid(colour)
            if value:
                colours[idx] = discord.Colour(value)
            else:
                invalid.append(colour)

        if len(invalid) > 1:
            return await ctx.send(f"Sorry, I don't know these colours: {' '.join(invalid)}")
        elif len(invalid) == 1:
            return await ctx.send(f"Sorry, I don't know the colour {invalid[0]}!")

        async with ctx.typing():
            # Expand list to 8 colours
            colours_n = len(colours)
            if colours_n < 8:
                q, r = divmod(8, colours_n)
                colours = colours * q + colours[:r]
            num = random.randint(1, 6)
            im = Image.open(Path(f"bot/resources/easter/easter_eggs/design{num}.png"))
            data = list(im.getdata())

            replaceable = {x for x in data if x not in IRREPLACEABLE}
            replaceable = sorted(replaceable, key=COLOURS.index)

            replacing_colours = {colour: colours[i] for i, colour in enumerate(replaceable)}
            new_data = []
            for x in data:
                if x in replacing_colours:
                    new_data.append((*replacing_colours[x].to_rgb(), 255))
                    # Also ensures that the alpha channel has a value
                else:
                    new_data.append(x)
            new_im = Image.new(im.mode, im.size)
            new_im.putdata(new_data)

            bufferedio = BytesIO()
            new_im.save(bufferedio, format="PNG")

            bufferedio.seek(0)

            file = discord.File(bufferedio, filename="egg.png")  # Creates file to be used in embed
            embed = discord.Embed(
                title="Your Colourful Easter Egg",
                description="Here is your pretty little egg. Hope you like it!"
            )
            embed.set_image(url="attachment://egg.png")
            embed.set_footer(text=f"Made by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        await ctx.send(file=file, embed=embed)
        return new_im


def setup(bot: commands.bot) -> None:
    """Egg decorating Cog load."""
    bot.add_cog(EggDecorating(bot))
    log.info("EggDecorating cog loaded.")

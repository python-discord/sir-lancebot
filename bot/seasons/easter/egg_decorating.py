import logging
import random
from io import BytesIO
from pathlib import Path


import discord
from PIL import Image
from discord.ext import commands

log = logging.getLogger(__name__)

COLOURS = [
    (255, 0, 0, 255), (255, 128, 0, 255), (255, 255, 0, 255), (0, 255, 0, 255),
    (0, 255, 255, 255), (0, 0, 255, 255), (255, 0, 255, 255), (128, 0, 128, 255)
]  # Colours to be replaced - Red, Orange, Yellow, Green, Light Blue, Dark Blue, Pink, Purple

IRREPLACEABLE = [
    (0, 0, 0, 0), (0, 0, 0, 255)
]  # Colours that are meant to stay the same - Transparent and Black


class EggDecorating(commands.Cog):
    """A Command that lets you decorate some easter eggs!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["decorateegg"])
    async def eggdecorate(self, ctx, *colours):
        """
        This 'paints' a beautiful egg using inputted colours

        It picks from a random set of designs and alters the colours to the user's liking
        """

        if len(colours) < 2:
            return await ctx.send("You must include at least 2 colours!")

        invalid = []
        converted = []
        for c in colours:
            try:
                colour = await commands.ColourConverter().convert(ctx, c)
                # Attempts to convert the arguments into discord.Colour
                converted.append(colour)
            except commands.BadArgument:
                invalid.append(c)

        if len(invalid) > 1:
            return await ctx.send(f"The following colours are invalid: {' '.join(invalid)}")
        elif len(invalid) == 1:
            return await ctx.send(f"{invalid[0]} is an invalid colour!")

        colours = converted

        async with ctx.typing():
            colours *= 4
            # This is to ensure that no IndexErrors are raised since the most amount of colours on an egg is 8
            num = random.randint(1, 6)
            im = Image.open(Path("bot", "resources", "easter", "easter_eggs", f"design{num}.png"))
            data = list(im.getdata())

            replaceable = {x for x in data if x not in IRREPLACEABLE}  # Turns it into a set to avoid duplicates
            replaceable = sorted(replaceable, key=COLOURS.index)  # Sorts it by colour order

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
            embed = discord.Embed(title="Your egg", description="Here is your pretty little egg. Hope you like it!")
            embed.set_image(url="attachment://egg.png")
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

            await ctx.send(file=file, embed=embed)


def setup(bot):
    """Cog load."""

    bot.add_cog(EggDecorating(bot))
    log.info("EggDecorating cog loaded.")

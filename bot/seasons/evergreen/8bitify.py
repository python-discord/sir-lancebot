from io import BytesIO

import discord
from PIL import Image
from discord.ext import commands


class EightBitify(commands.Cog):
    """Make your avatar 8bit!"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def pixelate(image: Image) -> Image:
        """Takes an image and pixelates it."""
        return image.resize((32, 32)).resize((1024, 1024))

    @staticmethod
    def quantize(image: Image) -> Image:
        """Reduces colour palette to 256 colours."""
        return image.quantize(colors=32)

    @commands.command(name="8bitify")
    async def eightbit_command(self, ctx: commands.Context) -> None:
        """Pixelates your avatar and changes the palette to an 8bit one."""
        async with ctx.typing():
            image_bytes = await ctx.author.avatar_url.read()
            avatar = Image.open(BytesIO(image_bytes))
            avatar = avatar.convert("RGBA").resize((1024, 1024))

            eightbit = self.pixelate(avatar)
            eightbit = self.quantize(eightbit)

            bufferedio = BytesIO()
            eightbit.save(bufferedio, format="PNG")
            bufferedio.seek(0)

            file = discord.File(bufferedio, filename="8bitavatar.png")

            embed = discord.Embed(
                title="Your 8-bit avatar",
                description='Here is your avatar. I think it looks all cool and "retro"'
            )

            embed.set_image(url="attachment://8bitavatar.png")
            embed.set_footer(text=f"Made by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        await ctx.send(file=file, embed=embed)


def setup(bot: commands.Bot) -> None:
    """Cog load."""
    bot.add_cog(EightBitify(bot))

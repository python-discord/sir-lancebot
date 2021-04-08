from io import BytesIO
from typing import Union

import discord
import matplotlib.pyplot as plt
from discord.ext import commands

# configure fonts and colors for matplotlib
plt.rcParams.update(
    {
        "font.size": 16,
        "mathtext.fontset": "cm",  # Computer Modern font set
        "mathtext.rm": "serif",
        "figure.facecolor": "38383F",  # matches Discord's dark mode background color
        "text.color": "white",
    }
)


class Latex(commands.Cog):
    """Renders latex."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _render(text: str) -> Union[BytesIO, str]:
        """Return the rendered image if latex compiles without errors, otherwise return the error message."""
        text = text.replace(r"\\", "$\n$")  # matplotlib uses \n for newlines, not \\
        fig = plt.figure()

        try:
            fig.text(0, 1, text, horizontalalignment="left", verticalalignment="top")

            rendered_image = BytesIO()
            plt.savefig(rendered_image, bbox_inches="tight", dpi=600)
            rendered_image.seek(0)
            return rendered_image

        except ValueError as e:
            return str(e)

    @commands.command()
    async def latex(self, ctx: commands.Context, *, text: str) -> None:
        """Renders the text in latex and sends the image."""
        async with ctx.typing():
            image = self._render(text)

            if isinstance(image, BytesIO):
                await ctx.send(file=discord.File(image, "latex.png"))
            else:
                await ctx.send(image)


def setup(bot: commands.Bot) -> None:
    """Load the Latex Cog."""
    bot.add_cog(Latex(bot))

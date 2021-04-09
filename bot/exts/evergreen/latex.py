import re
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

FORMATTED_CODE_REGEX = re.compile(
    r"(?P<delim>(?P<block>```)|``?)"  # code delimiter: 1-3 backticks; (?P=block) only matches if it's a block
    r"(?(block)(?:(?P<lang>[a-z]+)\n)?)"  # if we're in a block, match optional language (only letters plus newline)
    r"(?:[ \t]*\n)*"  # any blank (empty or tabs/spaces only) lines before the code
    r"(?P<code>.*?)"  # extract all code inside the markup
    r"\s*"  # any more whitespace before the end of the code markup
    r"(?P=delim)",  # match the exact same delimiter from the start again
    re.DOTALL | re.IGNORECASE,  # "." also matches newlines, case insensitive
)


class Latex(commands.Cog):
    """Renders latex."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _render(text: str) -> Union[BytesIO, str]:
        """Return the rendered image if latex compiles without errors, otherwise return the error message."""
        fig = plt.figure()

        try:
            fig.text(0, 1, text, horizontalalignment="left", verticalalignment="top")

            rendered_image = BytesIO()
            plt.savefig(rendered_image, bbox_inches="tight", dpi=600)
            rendered_image.seek(0)
            return rendered_image

        except ValueError as e:
            return str(e)

    @staticmethod
    def _prepare_input(text: str) -> str:
        text = text.replace(r"\\", "$\n$")  # matplotlib uses \n for newlines, not \\

        if match := FORMATTED_CODE_REGEX.match(text):
            return match.group("code")
        else:
            return text

    @commands.command()
    async def latex(self, ctx: commands.Context, *, text: str) -> None:
        """Renders the text in latex and sends the image."""
        text = self._prepare_input(text)
        async with ctx.typing():
            image = self._render(text)

            if isinstance(image, BytesIO):
                await ctx.send(file=discord.File(image, "latex.png"))
            else:
                await ctx.send("```" + image + "```")


def setup(bot: commands.Bot) -> None:
    """Load the Latex Cog."""
    bot.add_cog(Latex(bot))

import random

from cowsay import char_names, get_output_string
from discord import Embed
from discord.ext import commands

from bot.constants import Colours, NEGATIVE_REPLIES


class Cowsay(commands.Cog):
    """Cog for the cowsay command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases=["cow"],
        help=f"""
        Generates a cowsay string and sends it. The available characters for cowsay are:

        {', '.join(char_names)}"""
    )
    async def cowsay(self, ctx: commands.Context, character: str = "Cow", *, text: str = None) -> None:
        """Builds a cowsay string and sends it to Discord."""
        if not text:
            text = f"I'm a {character.lower()}"
        text = text.lower()
        character = character.lower()
        if len(text) >= 150:
            embed = Embed(
                title=random.choice(NEGATIVE_REPLIES),
                description="The given text is too long! Please submit something under 150 characters.",
                color=Colours.soft_red
            )
            await ctx.send(embed=embed)
            return

        try:
            msgbody = get_output_string(character, text)
        except Exception:
            embed = Embed(
                title=random.choice(NEGATIVE_REPLIES),
                description="That is an invalid character! Please enter a valid one.",
                color=Colours.soft_red
            )
            await ctx.send(embed=embed)
            return
        # These characters break the message limit, so we say no
        if character in ["dragon", "trex", "stegosaurus"]:
            embed = Embed(
                title=random.choice(NEGATIVE_REPLIES),
                description="The given character is invalid! Please submit a valid character.",
                color=Colours.soft_red
            )
            await ctx.send(embed=embed)
            return
        await ctx.send(f"```\n{msgbody}\n```")


def setup(bot: commands.Bot) -> None:
    """Loads cowsay cog."""
    bot.add_cog(Cowsay(bot))

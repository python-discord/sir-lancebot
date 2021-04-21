from random import choice

from cowsay import get_output_string
from discord import Embed
from discord.ext import commands

from bot.constants import Colours, NEGATIVE_REPLIES


class Cowsay(commands.Cog):
    """Cog for the cowsay command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["cow"])
    async def cowsay(self, ctx: commands.Context, character: str = "Cow", *, text: str = "I'm a Cow") -> None:
        """
        Generates some cowsay ASCII art and sends it in Discord.

        There are multiple character options to choose from. Here is a list:

        Cow
        Dragon
        Cheese
        Beavis
        Daemon
        Ghostbusters
        Kitty
        Meow
        Milk
        Pig
        Stegosaurus
        Stimpy
        Turkey
        Turtle
        Tux
        """
        text = text.lower()
        character = character.lower()
        if len(text) >= 150:
            embed = Embed(
                title=choice(NEGATIVE_REPLIES),
                description="The given text is too long! Please submit something under 150 characters.",
                color=Colours.soft_red
            )
            await ctx.send(embed=embed)
            return
            
        try:
            msgbody = get_output_string(character, text)
        except Exception:
            embed = Embed(
                title=choice(NEGATIVE_REPLIES),
                description="That is an invalid character! Please enter a valid one.",
                color=Colours.soft_red
            )
            await ctx.send(embed=embed)
            return
            
        await ctx.send(f"```\n{msgbody}\n```")


def setup(bot: commands.Bot) -> None:
    """Loads cowsay cog."""
    bot.add_cog(Cowsay(bot))

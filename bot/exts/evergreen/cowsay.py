from cowsay import get_output_string
from discord.ext import commands


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
        Trex
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
        msgbody = get_output_string(character, text)
        for character in msgbody:
            if character == " ":
                character += ""
        await ctx.send(f"```\n{msgbody}\n```")


def setup(bot: commands.Bot) -> None:
    """Loads cowsay cog."""
    bot.add_cog(Cowsay(bot))

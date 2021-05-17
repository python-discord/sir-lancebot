from contextlib import suppress

from cowsay import char_names, get_output_string
from discord import HTTPException
from discord.ext import commands

from bot.bot import Bot

# Creates a local copy of char_names to filter out unsupported characters.
localcharnames = list(char_names)
for element in ["dragon", "trex", "stegosaurus", "turkey", "ghostbusters"]:
    localcharnames.remove(element)


class Cowsay(commands.Cog):
    """Cog for the cowsay command."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(
        aliases=["cow"],
        help=f"""
        Generates a cowsay string and sends it. The available characters for cowsay are:

        {', '.join(localcharnames)}"""
    )
    async def cowsay(self, ctx: commands.Context, character: str = "Cow", *, text: str = None) -> None:
        """Builds a cowsay string and sends it to Discord."""
        if not text:
            text = f"I'm a {character.lower()}"
        character = character.lower()
        if len(text) >= 150:
            raise commands.BadArgument("The given text is too long! Please submit something under 150 characters.")

        try:
            msgbody = get_output_string(character, text)
        except Exception:
            raise commands.BadArgument("That is an invalid character! Please enter a valid one.")
        # These characters break the message limit, so we say no
        if character in ["dragon", "trex", "stegosaurus", "turkey", "ghostbusters"]:
            raise commands.BadArgument("The given character cannot be used! Please enter a valid character.")
        with suppress(HTTPException):
            await ctx.send(f"```\n{msgbody}\n```")


def setup(bot: Bot) -> None:
    """Loads cowsay cog."""
    bot.add_cog(Cowsay(bot))

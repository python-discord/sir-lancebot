from contextlib import suppress
from typing import Optional

from cowsay import char_names, get_output_string
from discord import HTTPException
from discord.ext import commands

from bot.bot import Bot

# Creates a local copy of char_names to filter out unsupported characters.
SUPPORTED_CHAR_NAMES = list(char_names)
for element in ["dragon", "trex", "stegosaurus", "turkey", "ghostbusters"]:
    SUPPORTED_CHAR_NAMES.remove(element)


class Cowsay(commands.Cog):
    """Cog for the cowsay command."""

    @commands.command(
        aliases=["cow"],
        help=f"""
        Generates a cowsay string and sends it. The available characters for cowsay are:

        {', '.join(SUPPORTED_CHAR_NAMES)}"""
    )
    async def cowsay(self, ctx: commands.Context, character: str = "Cow", *, text: Optional[str]) -> None:
        """Builds a cowsay string and sends it to Discord."""
        if not text:
            text = f"I'm a {character.lower()}"
        character = character.lower()
        if len(text) >= 150:
            raise commands.BadArgument("The given text is too long! Please submit something under 150 characters.")

        if character not in SUPPORTED_CHAR_NAMES:
            raise commands.BadArgument("The given character cannot be used! Please enter a valid character.")
        else:
            msgbody = get_output_string(character, text)

        with suppress(HTTPException):
            await ctx.send(f"```\n{msgbody}\n```")


def setup(bot: Bot) -> None:
    """Loads cowsay cog."""
    bot.add_cog(Cowsay(bot))

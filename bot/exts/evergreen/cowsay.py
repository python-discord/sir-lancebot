from contextlib import suppress
from typing import Optional

from cowsay import char_names, get_output_string
from discord import HTTPException
from discord.ext import commands

from bot.bot import Bot

# Creates a copy of supported cowsay character names to filter out characters which break the embed.
SUPPORTED_CHAR_NAMES = list(char_names)
for element in ["dragon", "trex", "stegosaurus", "turkey", "ghostbusters", "turtle"]:
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
        character = character.lower()
        if not text:
            text = f"I'm a {character}"
        if "```" in text:
            raise commands.BadArgument("Please do not use codeblocks, it breaks the command.")
        if len(text) >= 150 and character != "beavis":
            raise commands.BadArgument("The given text is too long! Please submit something under 150 characters.")
        elif len(text) >= 100 and character == "beavis":
            raise commands.BadArgument("The given text is too long! Please submit something under 100 characters.")

        if character not in SUPPORTED_CHAR_NAMES:
            raise commands.BadArgument("The given character cannot be used! Please enter a valid character.")
        else:
            msgbody = get_output_string(character, text)

        try:
            await ctx.send(f"```\n{msgbody}\n```")
        except HTTPException:
            raise commands.BadArgument("The message given for the specified character was too long! Please use something shorter.")


def setup(bot: Bot) -> None:
    """Load the Cowsay Cog."""
    bot.add_cog(Cowsay(bot))

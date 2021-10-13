from cowpy import cow
from discord.ext import commands

from bot.bot import Bot

SUPPORTED_COWS = []

for element in cow.get_cowacters():
    # The cows in the list are too big for Discord or innapropriate
    if element[0] not in ["turtle", "stegosaurus", "ghostbusters", "turkey", "mutilated", "kiss"]:
        SUPPORTED_COWS.append(element[0] if element[0] != "default" else "cow")


class Cowsay(commands.Cog):
    """Cog for the Cowsay command."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(
        help=f"""
        Generates a cowsay string and sends it. The available characters are:

        {', '.join(SUPPORTED_COWS)}"""
    )
    async def cowsay(self, ctx: commands.Context, cowtype: str = "cow", message: str = None) -> None:
        """Builds a cowsay string and sends it to discord."""
        if message is None:
            message = f"I'm a {cowtype}"

        if cowtype == "cow":
            cowtype = "default"

        if cowtype not in SUPPORTED_COWS:
            raise commands.BadArgument("The cow submitted is invalid! Please use a valid cow.")
        rawcow = cow.get_cow(cowtype)
        message = message.replace("`", "`\u200b")

        # Checks if message is too long
        if len(message) >= 150 and cowtype != "beavis":
            raise commands.BadArgument("The given text is too long! Please submit something under 150 characters.")

        elif len(message) >= 100 and cowtype == "beavis":
            raise commands.BadArgument("The given text is too long! Please submit something under 100 characters.")

        # Tries to get the cow class.
        try:
            truecow = rawcow()
        except TypeError:
            raise commands.BadArgument("The cow submitted is invalid! Please use a valid cow.")
        await ctx.send(f"```{truecow.milk(message)}```")


def setup(bot: Bot) -> None:
    """Loads the cowsay cog."""
    bot.add_cog(Cowsay(bot))

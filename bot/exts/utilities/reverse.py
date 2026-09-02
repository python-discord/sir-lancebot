
import discord
from discord import Interaction, app_commands
from discord.ext import commands

from bot.bot import Bot


class Reverse(commands.Cog):
    """Reverse the input text."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @app_commands.command(name="reverse")
    @app_commands.describe(text="The text to reverse.")
    async def reverse(self, ctx: Interaction, text: str) -> None:
        """Reverses the input text."""
        await ctx.response.send_message(f"> {text[::-1]}", allowed_mentions=discord.AllowedMentions.none())


async def setup(bot: Bot) -> None:
    """Load the Epoch cog."""
    await bot.add_cog(Reverse(bot))

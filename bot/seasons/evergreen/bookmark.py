import logging
import random

import discord
from discord.ext import commands

from bot.constants import Colours, ERROR_REPLIES

log = logging.getLogger(__name__)


class Bookmark(commands.Cog):
    """A cog that creates personal bookmarks by relaying a message to the user's DMs."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="bookmark", aliases=("bm", "pin"))
    async def bookmark(self, ctx: commands.Context, target_message: discord.Message, *,
                       title: str = "Bookmark") -> None:
        """Send you a link to the provided message in DM."""
        log.info(f"{ctx.author} bookmarked {target_message.jump_url} with hints {title}.")

        embed = discord.Embed(title="Your bookmark", colour=Colours.soft_green)

        if not title:
            title = "No hint provided."

        embed.set_author(name=target_message.author)
        embed.add_field(name='Content', value=target_message.content, inline=False)
        embed.add_field(name='Hints', value=title, inline=False)
        embed.add_field(name='Link', value=target_message.jump_url, inline=False)
        embed.set_author(name=target_message.author, icon_url=target_message.author.avatar_url)
        # embed.set_image()
        try:
            await ctx.author.send(embed=embed)
        except discord.Forbidden:
            embed_error = discord.Embed(
                title=random.choice(ERROR_REPLIES),
                description="You have to enable direct messages from this server to receive DMs from me.",
                colour=Colours.soft_red
            )
            await ctx.send(embed=embed_error)
            return
        await ctx.send("Bookmark sent to your DMs.")


def setup(bot: commands.Bot) -> None:
    """Bookmark Cog load."""
    bot.add_cog(Bookmark(bot))
    log.info("Bookmark cog loaded")

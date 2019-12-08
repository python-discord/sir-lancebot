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

        if not title:
            title = "No hint provided."

        embed = discord.Embed(
            title=title,
            colour=Colours.soft_green,
            description=f"{target_message.content} \n\n[Give it a visit.]({target_message.jump_url})"
        )
        embed.set_author(name=target_message.author)
        embed.set_author(name=target_message.author, icon_url=target_message.author.avatar_url)
        embed.set_thumbnail(url="https://img.icons8.com/color/48/FF3333/"
                            "bookmark-ribbon.png")
        embed.set_footer(text=f"{ctx.author}")
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
        await ctx.send("Bookmark sent to your DM.")


def setup(bot: commands.Bot) -> None:
    """Bookmark Cog load."""
    bot.add_cog(Bookmark(bot))
    log.info("Bookmark cog loaded")

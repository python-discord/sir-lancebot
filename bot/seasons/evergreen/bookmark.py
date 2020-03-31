import asyncio
import logging
import random
from copy import deepcopy

import discord
from discord.ext import commands

from bot.constants import Colours, ERROR_REPLIES, Emojis, bookmark_icon_url

log = logging.getLogger(__name__)


class Bookmark(commands.Cog):
    """Creates personal bookmarks by relaying a message link to the user's DMs."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="bookmark", aliases=("bm", "pin"))
    async def bookmark(
        self,
        ctx: commands.Context,
        target_message: discord.Message = None,
        *,
        title: str = "Bookmark"
    ) -> None:
        """Send the author a link to `target_message` via DMs. If Nothing is provided it take the commanding message."""
        if target_message is None:
            target_message = ctx.message

        # Prevent users from bookmarking a message in a channel they don't have access to
        permissions = ctx.author.permissions_in(target_message.channel)
        if not permissions.read_messages:
            log.info(f"{ctx.author} tried to bookmark a message in #{target_message.channel} but has no permissions.")
            embed = discord.Embed(
                title=random.choice(ERROR_REPLIES),
                color=Colours.soft_red,
                description="You don't have permission to view this channel."
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=title,
            colour=Colours.soft_green,
            description=target_message.content
        )
        embed.add_field(name="Wanna give it a visit?", value=f"[Visit original message]({target_message.jump_url})")
        embed.set_author(name=target_message.author, icon_url=target_message.author.avatar_url)
        embed.set_thumbnail(url=bookmark_icon_url)

        error_embed = discord.Embed(
            title=random.choice(ERROR_REPLIES),
            description=f"Please enable DMs to receive the bookmark. "
                        f"Once done you can retry by reacting with {Emojis.pin}",
            colour=Colours.soft_red
        )

        try:
            await ctx.author.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(embed=error_embed, delete_after=7.5)
            sent_person = set()
        else:
            await ctx.message.add_reaction(Emojis.envelope)
            sent_person = {ctx.author}  # set of id who got the message

        log.info(f"{ctx.author} bookmarked {target_message.jump_url} with title '{title}'.")
        await ctx.message.add_reaction(Emojis.pin)

        copied_embed = deepcopy(embed)

        copied_embed.add_field(
            name=f'Bookmarked from {ctx.author.name}.',
            value=f'[Visit original message]({ctx.message.jump_url})',
            inline=False
        )

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                user != self.bot.user
                and reaction.emoji == Emojis.pin
                and reaction.message == ctx.message
                and user not in sent_person
            )

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.message.clear_reactions()
                return

            log.info(f"{user.name} bookmarked {target_message.jump_url} with title '{title}' from '{ctx.author}'.")

            try:
                if user == ctx.author:
                    await user.send(embed=embed)
                else:
                    await user.send(embed=copied_embed)

            except discord.Forbidden:
                await ctx.send(f"{user.mention} Please enable your DM to receive the message.", delete_after=7.5)
                try:
                    await reaction.remove(user)
                except discord.Forbidden:
                    await ctx.send("I don't have permissions to remove reaction.", delete_after=7.5)
                except discord.HTTPException:
                    await ctx.send("Unknown error while removing reaction.", delete_after=7.5)

            except discord.HTTPException:
                await ctx.send("Unknown error while sending bookmark to user.", delete_after=7.5)

            else:
                sent_person.add(user)


def setup(bot: commands.Bot) -> None:
    """Load the Bookmark cog."""
    bot.add_cog(Bookmark(bot))
    log.info("Bookmark cog loaded.")

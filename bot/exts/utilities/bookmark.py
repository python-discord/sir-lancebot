import asyncio
import logging
import random
from typing import Optional

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, ERROR_REPLIES, Icons, Roles
from bot.utils.converters import WrappedMessageConverter
from bot.utils.decorators import whitelist_override

log = logging.getLogger(__name__)

# Number of seconds to wait for other users to bookmark the same message
TIMEOUT = 120
BOOKMARK_EMOJI = "📌"
MESSAGE_NOT_FOUND_ERROR = (
    "You must either provide a reference to a valid message, or reply to one."
    "\n\nThe lookup strategy for a message is as follows (in order):"
    "\n1. Lookup by '{channel ID}-{message ID}' (retrieved by shift-clicking on 'Copy ID')"
    "\n2. Lookup by message ID (the message **must** be in the current channel)"
    "\n3. Lookup by message URL"
)


class Bookmark(commands.Cog):
    """Creates personal bookmarks by relaying a message link to the user's DMs."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def build_bookmark_dm(target_message: discord.Message, title: str) -> discord.Embed:
        """Build the embed to DM the bookmark requester."""
        embed = discord.Embed(
            title=title,
            description=target_message.content,
            colour=Colours.soft_green
        )
        embed.add_field(
            name="Wanna give it a visit?",
            value=f"[Visit original message]({target_message.jump_url})"
        )
        embed.set_author(name=target_message.author, icon_url=target_message.author.display_avatar.url)
        embed.set_thumbnail(url=Icons.bookmark)

        return embed

    @staticmethod
    def build_error_embed(message: str) -> discord.Embed:
        """Builds an error embed for a given message."""
        return discord.Embed(
            title=random.choice(ERROR_REPLIES),
            description=message,
            colour=Colours.soft_red
        )

    async def action_bookmark(
        self,
        channel: discord.TextChannel,
        member: discord.Member,
        target_message: discord.Message,
        title: str
    ) -> None:
        """
        Sends the given target_message as a bookmark to the member in DMs to the user.

        Send an error embed instead if the member has DMs disabled.
        """
        embed = self.build_bookmark_dm(target_message, title)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            error_embed = self.build_error_embed(f"{member.mention}, please enable your DMs to receive the bookmark.")
            await channel.send(embed=error_embed)
        else:
            log.info(f"{member} bookmarked {target_message.jump_url} with title '{title}'")

    @commands.group(name="bookmark", aliases=("bm", "pin"), invoke_without_command=True)
    @commands.guild_only()
    @whitelist_override(roles=(Roles.everyone,))
    async def bookmark(
        self,
        ctx: commands.Context,
        target_message: Optional[WrappedMessageConverter],
        *,
        title: str = "Bookmark"
    ) -> None:
        """
        Send the author a link to the specified message via DMs.

        Members can either give a message as an argument, or reply to a message.

        Bookmarks can subsequently be deleted by using the `bookmark delete` command in DMs.
        """
        target_message: Optional[discord.Message] = target_message or getattr(ctx.message.reference, "resolved", None)
        if target_message is None:
            raise commands.UserInputError(MESSAGE_NOT_FOUND_ERROR)

        # Prevent users from bookmarking a message in a channel they don't have access to
        permissions = target_message.channel.permissions_for(ctx.author)
        if not permissions.read_messages:
            log.info(f"{ctx.author} tried to bookmark a message in #{target_message.channel} but has no permissions.")
            embed = self.build_error_embed(f"{ctx.author.mention} You don't have permission to view this channel.")
            await ctx.send(embed=embed)
            return

        await self.action_bookmark(ctx.channel, ctx.author, target_message, title)

        # Keep track of who has already bookmarked, so users can't spam reactions and cause loads of DMs
        bookmarked_users = [ctx.author.id]

        reaction_embed = discord.Embed(
            description=(
                f"React with {BOOKMARK_EMOJI} to be sent your very own bookmark to "
                f"[this message]({ctx.message.jump_url})."
            ),
            colour=Colours.soft_green
        )
        reaction_message = await ctx.send(embed=reaction_embed)
        await reaction_message.add_reaction(BOOKMARK_EMOJI)

        def event_check(reaction: discord.Reaction, user: discord.Member) -> bool:
            """Make sure that this reaction is what we want to operate on."""
            return (
                # Conditions for a successful pagination:
                all((
                    # Reaction is on this message
                    reaction.message.id == reaction_message.id,
                    # User has not already bookmarked this message
                    user.id not in bookmarked_users,
                    # Reaction is the `BOOKMARK_EMOJI` emoji
                    str(reaction.emoji) == BOOKMARK_EMOJI,
                    # Reaction was not made by the Bot
                    user.id != self.bot.user.id
                ))
            )

        while True:
            try:
                _, user = await self.bot.wait_for("reaction_add", timeout=TIMEOUT, check=event_check)
            except asyncio.TimeoutError:
                log.debug("Timed out waiting for a reaction")
                break
            log.trace(f"{user} has successfully bookmarked from a reaction, attempting to DM them.")
            await self.action_bookmark(ctx.channel, user, target_message, title)
            bookmarked_users.append(user.id)

        await reaction_message.delete()

    @bookmark.command(name="delete", aliases=("del", "rm"), root_aliases=("unbm", "unbookmark", "dmdelete", "dmdel"))
    @whitelist_override(bypass_defaults=True, allow_dm=True)
    async def delete_bookmark(
        self,
        ctx: commands.Context,
    ) -> None:
        """
        Delete the Sir-Lancebot message that the command invocation is replying to.

        This command allows deleting any message sent by Sir-Lancebot in the user's DM channel with the bot.
        The command invocation must be a reply to the message that is to be deleted.
        """
        target_message: Optional[discord.Message] = getattr(ctx.message.reference, "resolved", None)
        if target_message is None:
            raise commands.UserInputError("You must reply to the message from Sir-Lancebot you wish to delete.")

        if not isinstance(ctx.channel, discord.DMChannel):
            raise commands.UserInputError("You can only run this command your own DMs!")
        elif target_message.channel != ctx.channel:
            raise commands.UserInputError("You can only delete messages in your own DMs!")
        elif target_message.author != self.bot.user:
            raise commands.UserInputError("You can only delete messages sent by Sir Lancebot!")

        await target_message.delete()


async def setup(bot: Bot) -> None:
    """Load the Bookmark cog."""
    await bot.add_cog(Bookmark(bot))

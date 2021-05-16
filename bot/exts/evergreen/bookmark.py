import asyncio
import logging
import random
import typing as t

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, ERROR_REPLIES, Icons
from bot.utils.converters import WrappedMessageConverter

log = logging.getLogger(__name__)

# Number of seconds to wait for other users to bookmark the same message
TIMEOUT = 120
BOOKMARK_EMOJI = "📌"


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
        embed.set_author(name=target_message.author, icon_url=target_message.author.avatar_url)
        embed.set_thumbnail(url=Icons.bookmark)

        return embed

    @staticmethod
    def build_error_embed(user: discord.Member) -> discord.Embed:
        """Builds an error embed for when a bookmark requester has DMs disabled."""
        return discord.Embed(
            title=random.choice(ERROR_REPLIES),
            description=f"{user.mention}, please enable your DMs to receive the bookmark.",
            colour=Colours.soft_red
        )

    async def action_bookmark(
        self,
        channel: discord.TextChannel,
        user: discord.Member,
        target_message: discord.Message,
        title: str
    ) -> None:
        """Sends the bookmark DM, or sends an error embed when a user bookmarks a message."""
        try:
            embed = self.build_bookmark_dm(target_message, title)
            await user.send(embed=embed)
        except discord.Forbidden:
            error_embed = self.build_error_embed(user)
            await channel.send(embed=error_embed)
        else:
            log.info(f"{user} bookmarked {target_message.jump_url} with title '{title}'")

    @staticmethod
    async def send_reaction_embed(
        channel: discord.TextChannel,
        target_message: discord.Message
    ) -> discord.Message:
        """Sends an embed, with a reaction, so users can react to bookmark the message too."""
        message = await channel.send(
            embed=discord.Embed(
                description=(
                    f"React with {BOOKMARK_EMOJI} to be sent your very own bookmark to "
                    f"[this message]({target_message.jump_url})."
                ),
                colour=Colours.soft_green
            )
        )

        await message.add_reaction(BOOKMARK_EMOJI)
        return message

    @commands.command(name="bookmark", aliases=("bm", "pin"))
    async def bookmark(
        self,
        ctx: commands.Context,
        target_message: t.Optional[WrappedMessageConverter],
        *,
        title: str = "Bookmark"
    ) -> None:
        """Send the author a link to `target_message` via DMs."""
        if not target_message:
            if not ctx.message.reference:
                raise commands.UserInputError("You must either provide a valid message to bookmark, or reply to one.")
            target_message = ctx.message.reference.resolved

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
        await self.action_bookmark(ctx.channel, ctx.author, target_message, title)

        # Keep track of who has already bookmarked, so users can't spam reactions and cause loads of DMs
        bookmarked_users = [ctx.author.id]
        reaction_message = await self.send_reaction_embed(ctx.channel, target_message)

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


def setup(bot: Bot) -> None:
    """Load the Bookmark cog."""
    bot.add_cog(Bookmark(bot))

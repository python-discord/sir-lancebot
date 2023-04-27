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

MESSAGE_NOT_FOUND_ERROR = (
    "You must either provide a reference to a valid message, or reply to one."
    "\n\nThe lookup strategy for a message is as follows (in order):"
    "\n1. Lookup by '{channel ID}-{message ID}' (retrieved by shift-clicking on 'Copy ID')"
    "\n2. Lookup by message ID (the message **must** be in the current channel)"
    "\n3. Lookup by message URL"
)


async def dm_bookmark(
    target_user: discord.Member | discord.User,
    target_message: discord.Message,
    title: str,
) -> None:
    """
    Sends the `target_message` as a bookmark to the `target_user` DMs, with `title` as the embed title..

    Raises ``discord.Forbidden`` if the user's DMs are closed.
    """
    embed = Bookmark.build_bookmark_dm(target_message, title)
    message_url_view = discord.ui.View().add_item(
        discord.ui.Button(label="View Message", url=target_message.jump_url)
    )
    await target_user.send(embed=embed, view=message_url_view)
    log.info(f"{target_user} bookmarked {target_message.jump_url} with title {title!r}")


class SendBookmark(discord.ui.View):
    """The button that sends the bookmark to other users."""

    def __init__(
        self,
        author: discord.Member,
        channel: discord.TextChannel,
        target_message: discord.Message,
        title: str,
    ):
        super().__init__()

        self.clicked = [author.id]
        self.channel = channel
        self.target_message = target_message
        self.title = title

    @discord.ui.button(label="Receive Bookmark", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """The button callback."""
        if interaction.user.id in self.clicked:
            await interaction.response.send_message(
                "You have already received a bookmark to that message.",
                ephemeral=True,
            )
            return

        try:
            await dm_bookmark(interaction.user, self.target_message, self.title)
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=Bookmark.build_error_embed("Enable your DMs to receive the bookmark."),
                ephemeral=True,
            )
        else:
            self.clicked.append(interaction.user.id)
            await interaction.response.send_message("You have received a bookmark to that message.", ephemeral=True)


class BookmarkForm(discord.ui.Modal):
    """The form where a user can fill in a custom title for their bookmark & submit it."""

    bookmark_title = discord.ui.TextInput(
        label="Choose a title for your bookmark (optional)",
        placeholder="Type your bookmark title here",
        default="Bookmark",
        max_length=50,
        min_length=0,
        required=False,
    )

    def __init__(self, message: discord.Message):
        super().__init__(timeout=1000, title="Name your bookmark")
        self.message = message

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Sends the bookmark embed to the user with the newly chosen title."""
        title = self.bookmark_title.value or self.bookmark_title.default
        try:
            await dm_bookmark(interaction.user, self.message, title)
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=Bookmark.build_error_embed("Enable your DMs to receive the bookmark."),
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            embed=Bookmark.build_success_reply_embed(self.message),
            ephemeral=True,
        )


class Bookmark(commands.Cog):
    """Creates personal bookmarks by relaying a message link to the user's DMs."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.book_mark_context_menu = discord.app_commands.ContextMenu(
            name="Bookmark",
            callback=self._bookmark_context_menu_callback,
        )
        self.bot.tree.add_command(self.book_mark_context_menu, guild=discord.Object(bot.guild_id))

    @staticmethod
    def build_success_reply_embed(target_message: discord.Message) -> discord.Embed:
        """Build the ephemeral reply embed to the bookmark requester."""
        return discord.Embed(
            description=(
                f"A bookmark for [this message]({target_message.jump_url}) has been successfully sent your way."
            ),
            colour=Colours.soft_green,
        )

    @staticmethod
    def build_bookmark_dm(target_message: discord.Message, title: str) -> discord.Embed:
        """Build the embed that is DM'd to the bookmark requester."""
        embed = discord.Embed(title=title, description=target_message.content, colour=Colours.soft_green)
        embed.set_author(
            name=target_message.author,
            icon_url=target_message.author.display_avatar.url,
        )
        embed.set_thumbnail(url=Icons.bookmark)
        return embed

    @staticmethod
    def build_error_embed(message: str) -> discord.Embed:
        """Builds an error embed for a given message."""
        return discord.Embed(
            title=random.choice(ERROR_REPLIES),
            description=message,
            colour=Colours.soft_red,
        )

    @staticmethod
    def build_bookmark_embed(target_message: discord.Message) -> discord.Embed:
        """Build the channel embed to the bookmark requester."""
        return discord.Embed(
            description=(
                f"Click the button to be sent your very own bookmark to "
                f"[this message]({target_message.jump_url})."
            ),
            colour=Colours.soft_green,
        )

    async def _bookmark_context_menu_callback(self, interaction: discord.Interaction, message: discord.Message) -> None:
        """The callback that will be invoked upon using the bookmark's context menu command."""
        permissions = interaction.channel.permissions_for(interaction.user)
        if not permissions.read_messages:
            log.info(
                f"{interaction.user} tried to bookmark a message in #{interaction.channel} but doesn't have permission."
            )
            embed = self.build_error_embed("You don't have permission to view this channel.")
            await interaction.response.send_message(embed=embed)
            return

        bookmark_title_form = BookmarkForm(message=message)
        await interaction.response.send_modal(bookmark_title_form)

    @commands.group(name="bookmark", aliases=("bm", "pin"), invoke_without_command=True)
    @commands.guild_only()
    @whitelist_override(roles=(Roles.everyone,))
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def bookmark(
        self,
        ctx: commands.Context,
        target_message: Optional[WrappedMessageConverter],
        *,
        title: str = "Bookmark",
    ) -> None:
        """
        Send the author a link to the specified message via DMs.

        Members can either give a message as an argument, or reply to a message.

        Bookmarks can subsequently be deleted by using the `bookmark delete` command in DMs.
        """
        target_message: Optional[discord.Message] = target_message or getattr(ctx.message.reference, "resolved", None)
        if target_message is None:
            raise commands.UserInputError(MESSAGE_NOT_FOUND_ERROR)

        permissions = ctx.channel.permissions_for(ctx.author)
        if not permissions.read_messages:
            log.info(f"{ctx.author} tried to bookmark a message in #{ctx.channel} but has no permissions.")
            embed = self.build_error_embed("You don't have permission to view this channel.")
            await ctx.send(embed=embed)
            return

        try:
            await dm_bookmark(ctx.author, target_message, title)
        except discord.Forbidden:
            error_embed = self.build_error_embed(
                    f"{ctx.author.mention}, please enable your DMs to receive the bookmark."
            )
            await ctx.send(embed=error_embed)
        else:
            log.info(f"{ctx.author.mention} bookmarked {target_message.jump_url} with title '{title}'")

        view = SendBookmark(ctx.author, ctx.channel, target_message, title)
        embed = self.build_bookmark_embed(target_message)

        await ctx.send(embed=embed, view=view, delete_after=180)

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

import logging
import random
from typing import Optional

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, ERROR_REPLIES, Icons, Roles
from bot.utils.decorators import whitelist_override

log = logging.getLogger(__name__)


class BookmarkTitleSelectionForm(discord.ui.Modal):
    """
    The form where a user can fill in a custom title for their bookmark & submit it.

    This form is only available when the command is invoked from a context menu.
    """

    bookmark_title = discord.ui.TextInput(
        label="Choose a title for your bookmark (optional)",
        placeholder="Type your bookmark title here",
        default="Bookmark",
        max_length=50,
        min_length=0,
        required=False
    )

    def __init__(
            self,
            message: discord.Message,
            action_bookmark_function: Callable[[discord.TextChannel, discord.Member, discord.Message, str], None],
    ):
        super().__init__(timeout=1000, title="Name your bookmark")
        self.message = message
        self.action_bookmark = action_bookmark_function

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Sends the bookmark embed to the user with the newly chosen title."""
        title = self.bookmark_title.value or self.bookmark_title.default
        await self.action_bookmark(interaction.channel, interaction.user, self.message, title)
        embed = Bookmark.build_ephemeral_bookmark_embed(self.message)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class LinkTargetMessage(discord.ui.View):
    """The button that relays the user to the bookmarked message."""

    def __init__(self, target_message: discord.Message):
        super().__init__()
        self.add_item(discord.ui.Button(label="View Message", url=target_message.jump_url))


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
    def build_ephemeral_bookmark_embed(target_message: discord.Message) -> discord.Embed:
        """Build the ephemeral embed to the bookmark requester."""
        return discord.Embed(
            description=(
                f"A bookmark for [this message]({target_message.jump_url}) "
                f"has been successfully sent your way.\n"
            ),
            colour=Colours.soft_green,
        )

    @staticmethod
    def build_bookmark_dm(target_message: discord.Message, title: str) -> discord.Embed:
        """Build the embed to DM the bookmark requester."""
        embed = discord.Embed(
            title=title,
            description=target_message.content,
            colour=Colours.soft_green
        )
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
            await member.send(embed=embed, view=LinkTargetMessage(target_message))
        except discord.Forbidden:
            error_embed = self.build_error_embed(f"{member.mention}, please enable your DMs to receive the bookmark.")
            await channel.send(embed=error_embed)
        else:
            log.info(f"{member} bookmarked {target_message.jump_url} with title '{title}'")

    async def _bookmark_context_menu_callback(self, interaction: discord.Interaction, message: discord.Message) -> None:
        """The callback that will be invoked upon using the bookmark's context menu command."""
        permissions = interaction.channel.permissions_for(interaction.user)
        if not permissions.read_messages:
            log.info(f"{interaction.user} tried to bookmark a message in #{interaction.channel}"
                     f"but has no permissions.")
            embed = Bookmark.build_error_embed("You don't have permission to view this channel.")
            await interaction.response.send_message(embed=embed)
            return

        bookmark_title_form = BookmarkTitleSelectionForm(
            message=message,
            action_bookmark_function=self.action_bookmark
        )
        await interaction.response.send_modal(bookmark_title_form)

    @commands.group(name="bookmark", aliases=("bm", "pin"), invoke_without_command=True)
    @commands.guild_only()
    @whitelist_override(roles=(Roles.everyone,))
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def bookmark(self, ctx: commands.Context) -> None:
        """Teach the invoker how to use the new context-menu based command for a smooth migration."""
        await ctx.send(
            embed=self.build_error_embed(
                "The bookmark text command has been replaced with a context menu command!\n\n"
                "To bookmark a message simply right-click (press and hold on mobile) "
                "on a message, open the 'Apps' menu, and click 'Bookmark'."
            )
        )

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

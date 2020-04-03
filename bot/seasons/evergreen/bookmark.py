import asyncio
import logging
import random
from copy import deepcopy
from typing import Union

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
            target: Union[discord.Message, discord.User],
            *,
            title: str = "Bookmark"
    ) -> None:
        """
        Send the author a link to `target_message` via DMs.

        A user mention can also be passed to get the user's last message in channel where the command is invoked.
        """
        if type(target) == discord.User:
            async for message in ctx.channel.history(limit=20):  # Takes last 2 messages from the channel.
                if message.author == target and message.id != ctx.message.id:
                    target = message
                    break

        if type(target) == discord.User:  # target is still User that means message not found
            log.info(f'{ctx.author.name} Tried to bookmark {target} message but no message was found.')
            await ctx.send(f'None of the previous 20 message is from {target.name}.', delete_after=7)
            return

        # Prevent users from bookmarking a message in a channel they don't have access to
        permissions = ctx.author.permissions_in(target.channel)
        if not permissions.read_messages:
            log.info(f"{ctx.author} tried to bookmark a message in #{target.channel} but has no permissions.")
            embed = discord.Embed(
                title=random.choice(ERROR_REPLIES),
                color=Colours.soft_red,
                description="You don't have permission to view this channel."
            )
            await ctx.send(embed=embed)
            return

        ctx.message.content = title  # tricking discord.py to use clean_content

        embed = discord.Embed(
            title=ctx.message.clean_content,
            colour=Colours.soft_green,
            description=target.content
        )
        embed.add_field(name="Wanna give it a visit?", value=f"[Visit original message]({target.jump_url})")
        embed.set_author(name=target.author, icon_url=target.author.avatar_url)
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

        log.info(f"{ctx.author} bookmarked {target.jump_url} with title '{title}'.")
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

            log.info(f"{user.name} tried bookmarking {target.jump_url} with title '{title}' from "
                     f"'{ctx.author}'.")

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
                await reaction.remove(user)

            else:
                sent_person.add(user)


def setup(bot: commands.Bot) -> None:
    """Load the Bookmark cog."""
    bot.add_cog(Bookmark(bot))
    log.info("Bookmark cog loaded.")

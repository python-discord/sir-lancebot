import textwrap

from discord import Color, Embed, Emoji
from discord.ext import commands

from bot.utils.time import time_since


class Emojis(commands.Cog):
    """Has commands related to emojis."""

    @commands.group(name="emoji", invoke_without_command=True)
    async def emojis_group(self, ctx: commands.Context, emoji: Emoji) -> None:
        """A group of commands related to emojis."""
        # No parameters = same as invoking info subcommand
        await ctx.invoke(self.info_command, emoji)

    @emojis_group.command(name="info")
    async def info_command(self, ctx: commands.Context, emoji: Emoji) -> None:
        """Returns relevant information about a Discord Emoji."""
        emoji_information = Embed(
            title=f'Information about "{emoji.name}"',
            description=textwrap.dedent(f"""
                Name: {emoji.name}
                Created: {time_since(emoji.created_at)}
                ID: {emoji.id}
                [Emoji source image]({emoji.url})
            """),
            color=Color.blurple()
        )
        emoji_information.set_thumbnail(
            url=emoji.url
        )
        await ctx.send(embed=emoji_information)


def setup(bot: commands.Bot) -> None:
    """Add the Emojis cog into the bot."""
    bot.add_cog(Emojis())

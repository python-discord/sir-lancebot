import inspect
from pathlib import Path
from typing import Optional, Tuple, Union

from discord import Embed
from discord.ext import commands

from bot.constants import Source

SourceType = Union[commands.Command, commands.Cog, str, commands.ExtensionNotLoaded]


class SourceConverter(commands.Converter):
    """Convert an argument into a help command, tag, command, or cog."""

    async def convert(self, ctx: commands.Context, argument: str) -> SourceType:
        """Convert argument into source object."""
        cog = ctx.bot.get_cog(argument)
        if cog:
            return cog

        cmd = ctx.bot.get_command(argument)
        if cmd:
            return cmd

        raise commands.BadArgument(
            f"Unable to convert `{argument}` to valid command or Cog."
        )


class BotSource(commands.Cog):
    """Displays information about the bot's source code."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="source", aliases=("src",))
    async def source_command(self, ctx: commands.Context, *, source_item: SourceConverter = None) -> None:
        """Display information and a GitHub link to the source code of a command, tag, or cog."""
        if not source_item:
            embed = Embed(title="Sir Lancebot's GitHub Repository")
            embed.add_field(name="Repository", value=f"[Go to GitHub]({Source.github})")
            embed.set_thumbnail(url=Source.github_avatar_url)
            await ctx.send(embed=embed)
            return

        embed = await self.build_embed(source_item)
        await ctx.send(embed=embed)

    def get_source_link(self, source_item: SourceType) -> Tuple[str, str, Optional[int]]:
        """
        Build GitHub link of source item, return this link, file location and first line number.

        Raise BadArgument if `source_item` is a dynamically-created object (e.g. via internal eval).
        """
        if isinstance(source_item, commands.Command):
            src = source_item.callback.__code__
            filename = src.co_filename
        else:
            src = type(source_item)
            try:
                filename = inspect.getsourcefile(src)
            except TypeError:
                raise commands.BadArgument("Cannot get source for a dynamically-created object.")

        if not isinstance(source_item, str):
            try:
                lines, first_line_no = inspect.getsourcelines(src)
            except OSError:
                raise commands.BadArgument("Cannot get source for a dynamically-created object.")

            lines_extension = f"#L{first_line_no}-L{first_line_no+len(lines)-1}"
        else:
            first_line_no = None
            lines_extension = ""

        file_location = Path(filename).relative_to(Path.cwd()).as_posix()

        url = f"{Source.github}/blob/master/{file_location}{lines_extension}"

        return url, file_location, first_line_no or None

    async def build_embed(self, source_object: SourceType) -> Optional[Embed]:
        """Build embed based on source object."""
        url, location, first_line = self.get_source_link(source_object)

        if isinstance(source_object, commands.Command):
            if source_object.cog_name == 'Help':
                title = "Help Command"
                description = source_object.__doc__.splitlines()[1]
            else:
                description = source_object.short_doc
                title = f"Command: {source_object.qualified_name}"
        else:
            title = f"Cog: {source_object.qualified_name}"
            description = source_object.description.splitlines()[0]

        embed = Embed(title=title, description=description)
        embed.set_thumbnail(url=Source.github_avatar_url)
        embed.add_field(name="Source Code", value=f"[Go to GitHub]({url})")
        line_text = f":{first_line}" if first_line else ""
        embed.set_footer(text=f"{location}{line_text}")

        return embed


def setup(bot: commands.Bot) -> None:
    """Load the BotSource cog."""
    bot.add_cog(BotSource(bot))

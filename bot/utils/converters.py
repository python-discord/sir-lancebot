from datetime import datetime
from typing import Tuple, Union

import discord
from discord.ext import commands


class WrappedMessageConverter(commands.MessageConverter):
    """A converter that handles embed-suppressed links like <http://example.com>."""

    @staticmethod
    async def convert(ctx: commands.Context, argument: str) -> discord.Message:
        """Wrap the commands.MessageConverter to handle <> delimited message links."""
        # It's possible to wrap a message in [<>] as well, and it's supported because its easy
        if argument.startswith("[") and argument.endswith("]"):
            argument = argument[1:-1]
        if argument.startswith("<") and argument.endswith(">"):
            argument = argument[1:-1]

        return await super().convert(ctx, argument)


class CoordinateConverter(commands.Converter):
    """Converter for Coordinates."""

    @staticmethod
    async def convert(ctx: commands.Context, coordinate: str) -> Tuple[int, int]:
        """Take in a coordinate string and turn it into an (x, y) tuple."""
        if len(coordinate) not in (2, 3):
            raise commands.BadArgument("Invalid co-ordinate provided.")

        coordinate = coordinate.lower()
        if coordinate[0].isalpha():
            digit = coordinate[1:]
            letter = coordinate[0]
        else:
            digit = coordinate[:-1]
            letter = coordinate[-1]

        if not digit.isdigit():
            raise commands.BadArgument

        x = ord(letter) - ord("a")
        y = int(digit) - 1

        if (not 0 <= x <= 9) or (not 0 <= y <= 9):
            raise commands.BadArgument
        return x, y


SourceType = Union[commands.Command, commands.Cog]


class SourceConverter(commands.Converter):
    """Convert an argument into a command or cog."""

    @staticmethod
    async def convert(ctx: commands.Context, argument: str) -> SourceType:
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


class DateConverter(commands.Converter):
    """Parse SOL or earth date (in format YYYY-MM-DD) into `int` or `datetime`. When invalid input, raise error."""

    @staticmethod
    async def convert(ctx: commands.Context, argument: str) -> Union[int, datetime]:
        """Parse date (SOL or earth) into `datetime` or `int`. When invalid value, raise error."""
        if argument.isdigit():
            return int(argument)
        try:
            date = datetime.strptime(argument, "%Y-%m-%d")
        except ValueError:
            raise commands.BadArgument(
                f"Can't convert `{argument}` to `datetime` in format `YYYY-MM-DD` or `int` in SOL."
            )
        return date

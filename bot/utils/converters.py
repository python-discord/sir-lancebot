from datetime import UTC, datetime

import discord
from discord.ext import commands


class WrappedMessageConverter(commands.MessageConverter):
    """A converter that handles embed-suppressed links like <http://example.com>."""

    async def convert(self, ctx: commands.Context, argument: str) -> discord.Message:
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
    async def convert(ctx: commands.Context, coordinate: str) -> tuple[int, int]:
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

        if not digit.isdecimal():
            raise commands.BadArgument

        x = ord(letter) - ord("a")
        y = int(digit) - 1

        if (not 0 <= x <= 9) or (not 0 <= y <= 9):
            raise commands.BadArgument
        return x, y


SourceType = commands.Command | commands.Cog


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
    async def convert(ctx: commands.Context, argument: str) -> int | datetime:
        """Parse date (SOL or earth) into `datetime` or `int`. When invalid value, raise error."""
        if argument.isdecimal():
            return int(argument)
        try:
            date = datetime.strptime(argument, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            raise commands.BadArgument(
                f"Can't convert `{argument}` to `datetime` in format `YYYY-MM-DD` or `int` in SOL."
            )
        return date


class Subreddit(commands.Converter):
    """Forces a string to begin with "r/" and checks if it's a valid subreddit."""

    @staticmethod
    async def convert(ctx: commands.Context, sub: str) -> str:
        """
        Force sub to begin with "r/" and check if it's a valid subreddit.

        If sub is a valid subreddit, return it prepended with "r/"
        """
        sub = sub.lower()

        if not sub.startswith("r/"):
            sub = f"r/{sub}"

        resp = await ctx.bot.http_session.get(
            "https://www.reddit.com/subreddits/search.json",
            params={"q": sub}
        )

        json = await resp.json()
        if not json["data"]["children"]:
            raise commands.BadArgument(
                f"The subreddit `{sub}` either doesn't exist, or it has no posts."
            )

        return sub

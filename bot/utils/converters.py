import discord
from discord.ext.commands import BadArgument, Context
from discord.ext.commands.converter import Converter, MessageConverter


class WrappedMessageConverter(MessageConverter):
    """A converter that handles embed-suppressed links like <http://example.com>."""

    async def convert(self, ctx: discord.ext.commands.Context, argument: str) -> discord.Message:
        """Wrap the commands.MessageConverter to handle <> delimited message links."""
        # It's possible to wrap a message in [<>] as well, and it's supported because its easy
        if argument.startswith("[") and argument.endswith("]"):
            argument = argument[1:-1]
        if argument.startswith("<") and argument.endswith(">"):
            argument = argument[1:-1]

        return await super().convert(ctx, argument)


class Subreddit(Converter):
    """Forces a string to begin with "r/" and checks if it's a valid subreddit."""

    @staticmethod
    async def convert(ctx: Context, sub: str) -> str:
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
            raise BadArgument(
                f"The subreddit `{sub}` either doesn't exist, or it has no posts."
            )

        return sub

import discord

from discord.ext.commands.converter import MessageConverter


class BetterMessageConverter(MessageConverter):
    """A converter that handles embed-suppressed links like <http://example.com>"""
    async def convert(self, ctx, argument: str) -> discord.Message:
        # It's possible to wrap a message in [<>] as well, and it's supported because its easy
        if argument.startswith("[") and argument.endswith("]"):
            argument = argument[1:-1]
        if argument.startswith("<") and argument.endswith(">"):
            argument = argument[1:-1]

        return await super().convert(ctx, argument)

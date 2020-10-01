import logging

from discord.ext import commands

log = logging.getLogger(__name__)


class EmojiCount(commands.Cog):
    """Command that give random emoji based on category."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ec")
    async def ec(self, ctx, emoj: str):
        """Returns embed with emoji category and info given by user."""
        emoji = []
        for a in ctx.guild.emojis:
            for n in a.name.split('_'):
                if len(n) == 1:
                    pass
                elif n.name[0] == emoji.lower():
                    emoji.append(a)
        await ctx.send(emoji)


def setup(bot: commands.Bot) -> None:
    """Emoji Count Cog load."""
    bot.add_cog(EmojiCount(bot))

from discord.ext import commands
from bot.bot import Bot


class Epoch(commands.Cog):

    @commands.command(name="epoch")
    async def epoch(self, ctx: commands.Context, *, time) -> None:
        pass


def setup(bot: Bot) -> None:
    bot.add_cog(Epoch())

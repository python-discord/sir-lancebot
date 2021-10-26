from collections import Counter
from datetime import datetime

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours


class Leaderboard(commands.Cog):
    """Get info about the bot's ping and uptime."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def ordinal_number(n: int) -> str:
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
        if 11 <= (n % 100) <= 13:
            suffix = "th"
        return str(n) + suffix

    @commands.command(aliases=("lb",))
    async def leaderboard(self, ctx: commands.Context) -> None:
        """Get the current top 10."""
        leaderboard = Counter()

        for cached_leaderboard in self.bot.games_leaderboard.values():
            _leaderboard: dict[int, int] = await cached_leaderboard.to_dict()
            leaderboard += Counter(_leaderboard)

        top_ten = leaderboard.most_common(10)

        lines = []
        for index, (member_id, score) in enumerate(top_ten, start=1):
            rank = format(self.ordinal_number(index), " >4")
            score = format(score, " >4")
            mention = f"<@{member_id}>"
            lines.append(f"`{rank} |  {score} |` {mention}")

        board_formatted = "\n".join(lines) if lines else "(no entries yet)"
        description = f"`Rank | Score |` Member\n{board_formatted}"

        embed = discord.Embed(
            title="Top 10",
            description=description,
            colour=Colours.orange,
            timestamp=datetime.utcnow(),
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/902160691509723208.png?size=96"
        )
        await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Load the Leaderboard cog."""
    bot.add_cog(Leaderboard(bot))

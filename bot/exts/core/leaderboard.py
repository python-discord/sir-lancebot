from collections import Counter
from datetime import datetime

import discord
from async_rediscache import RedisCache
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours


class Leaderboard(commands.Cog):
    """Cog for getting game leaderboards."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def ordinal_number(n: int) -> str:
        """Get the ordinal number for `n`."""
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
        if 11 <= (n % 100) <= 13:
            suffix = "th"
        return str(n) + suffix

    async def make_leaderboard(self, cached_leaderboard: list[RedisCache]) -> discord.Embed:
        """Make a discord embed for the current top 10 members in the cached leaderboard."""
        if len(cached_leaderboard) == 1:
            game_leaderboard = await cached_leaderboard[0].to_dict()
            leaderboard = Counter(game_leaderboard)
        else:
            leaderboard = Counter()
            for lb in cached_leaderboard:
                game_leaderboard = await lb.to_dict()
                leaderboard += Counter(game_leaderboard)

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

        return embed

    @commands.group(aliases=("lb",), invoke_without_command=True)
    async def leaderboard(self, ctx: commands.Context, game: str = None) -> None:
        """Get overall leaderboard if not game specified, else leaderboard for that game."""
        if ctx.invoked_subcommand:
            return

        if game:
            leaderboards = self.bot.games_leaderboard.get(game)
            await ctx.send(", ".join(self.bot.games_leaderboard.keys()))
            if not leaderboards:
                raise commands.BadArgument(f"Leaderboard for game {game} not found.")
            leaderboard = [leaderboards[0]]
        else:
            leaderboard = [lb for lb, _ in self.bot.games_leaderboard.values()]

        embed = await self.make_leaderboard(leaderboard)
        await ctx.send(embed=embed)

    @leaderboard.command(name="today", aliases=("t",))
    async def per_day_leaderboard(self, ctx: commands.Context, game: str = None) -> None:
        """Get today's overall leaderboard if not game specified, else leaderboard for that game."""
        if game:
            leaderboards = self.bot.games_leaderboard.get(game)
            if not leaderboards:
                raise commands.BadArgument(f"Leaderboard for game {game} not found.")
            leaderboard = [leaderboards[1]]
        else:
            leaderboard = [lb for _, lb in self.bot.games_leaderboard.values()]

        embed = await self.make_leaderboard(leaderboard)
        await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Load the Leaderboard cog."""
    bot.add_cog(Leaderboard(bot))

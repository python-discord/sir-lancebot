from random import choice

from discord.ext import commands

from bot.bot import Bot

CHOICES = ["rock", "paper", "scissors"]
SHORT_CHOICES = ["r", "p", "s"]

# Using a dictionary instead of conditions to check for the winner.
WINNER_DICT = {
    "r": {
        "r": 0,
        "p": -1,
        "s": 1,
    },
    "p": {
        "r": 1,
        "p": 0,
        "s": -1,
    },
    "s": {
        "r": -1,
        "p": 1,
        "s": 0,
    }
}


class RPS(commands.Cog):
    """Rock Paper Scissors. The Classic Game!"""

    @commands.command(case_insensitive=True)
    async def rps(self, ctx: commands.Context, move: str) -> None:
        """Play the classic game of Rock Paper Scissors with your own sir-lancebot!"""
        move = move.lower()
        player_mention = ctx.author.mention

        if move not in CHOICES and move not in SHORT_CHOICES:
            raise commands.BadArgument(f"Invalid move. Please make move from options: {', '.join(CHOICES).upper()}.")

        bot_move = choice(CHOICES)
        # value of player_result will be from (-1, 0, 1) as (lost, tied, won).
        player_result = WINNER_DICT[move[0]][bot_move[0]]

        if player_result == 0:
            message_string = f"{player_mention} You and Sir Lancebot played {bot_move}, it's a tie."
            await ctx.send(message_string)
        elif player_result == 1:
            await ctx.send(f"Sir Lancebot played {bot_move}! {player_mention} won!")
        else:
            await ctx.send(f"Sir Lancebot played {bot_move}! {player_mention} lost!")


async def setup(bot: Bot) -> None:
    """Load the RPS Cog."""
    await bot.add_cog(RPS(bot))

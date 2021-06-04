from random import choice

from discord import Member, TextChannel
from discord.ext import commands

from bot.bot import Bot


CHOICES = ['rock', 'paper', 'scissor']
SHORT_CHOICES = ['r', 'p', 's']

# Using a dictionary instead of conditions to check for the winner.
WINNER_DICT = {
    'r': {
        'r': 0,
        'p': -1,
        's': 1,
    },
    'p': {
        'r': 1,
        'p': 0,
        's': -1,
    },
    's': {
        'r': -1,
        'p': 1,
        's': 0,
    }
}


class RPS(commands.Cog):
    """Rock Paper Scissor. The Classic Game!"""

    @staticmethod
    def get_winner(action_one: str, action_two: str) -> int:
        """Returns result of match from (-1, 0, 1) as (lost, tied, won)."""
        return WINNER_DICT[action_one][action_two]

    @staticmethod
    def make_move() -> str:
        """Returns random move for bot from CHOICES."""
        return choice(CHOICES)

    async def game_start(self, player: Member, channel: TextChannel, action: str) -> None:
        """
        Check action of player, draw a move and return result.

        After checking if action of player is valid, make a random move.
        And based on the move, compare moves of both player and bot and send approprite result.
        """
        if not action:
            await channel.send("Please make a move.")
            return

        action = action.lower()

        if action not in CHOICES and action not in SHORT_CHOICES:
            await channel.send(f"Invalid move. Please make move from options: {' '.join(CHOICES)}")
            return

        bot_move = self.make_move()
        player_result = self.get_winner(action[0], bot_move[0])

        if player_result == 0:
            message_string = f"{player.mention} You and Sir Lancebot played {bot_move.upper()}, It's a tie."
            await channel.send(message_string)
        elif player_result == 1:
            await channel.send(f"Sir Lancebot played {bot_move.upper()}! {player.mention} Won!")
        else:
            await channel.send(f"Sir Lancebot played {bot_move.upper()}! {player.mention} Lost!")

    @commands.command(case_insensitive=True)
    async def rps(self, ctx: commands.Context, move: str) -> None:
        """Play the classic game of Rock Paper Scissor with your own sir-lancebot!"""
        await self.game_start(ctx.author, ctx.channel, move)


def setup(bot: Bot) -> None:
    """Load RPS Cog."""
    bot.add_cog(RPS(bot))

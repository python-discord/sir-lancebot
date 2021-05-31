import random
from bot.bot import Bot
import discord
from discord.ext import commands
from discord.ext.commands import guild_only

choices = ['rock', 'paper', 'scissor']
short_choices = ['r', 'p', 's']
"""
Instead of putting bunch of conditions to check winner,
We can just manage this dictionary
"""
winner = {
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


class Game:
    """A Rock Paper Scissors Game."""
    def __init__(
        self,
        channel: discord.TextChannel,
    ) -> None:
        self.channel = channel

    @staticmethod
    def get_winner(action_one, action_two):
        return winner[action_one][action_two]

    @staticmethod
    def make_move() -> str:
        """Return move"""
        return random.choice(choices)

    async def game_start(self, player, action) -> None:
        if not action:
            return await self.channel.send("Please make a move.")
        action = action.lower()
        if action not in choices and action not in short_choices:
            return await self.channel.send(f"Invalid move. Please make move from options: {' '.join(choices)}")
        bot_move = self.make_move()
        player_result = self.get_winner(action[0], bot_move[0])
        if player_result == 0:
            message_string = f"{player.mention} You and Sir Lancebot played {bot_move.upper()}, It's a tie."
            return await self.channel.send(message_string)
        elif player_result == 1:
            return await self.channel.send(f"Sir Lancebot played {bot_move.upper()}! {player.mention} Won!")
        else:
            return await self.channel.send(f"Sir Lancebot played {bot_move.upper()}! {player.mention} Lost!")


class RPS(commands.Cog):
    """Rock Paper Scissor. The Classic Game!"""
    """
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
    """
    async def _play_game(
        self,
        ctx: commands.Context,
        move: str
    ) -> None:
        """Helper for playing RPS."""
        game = Game(ctx.channel)
        await game.game_start(ctx.author, move)

    @guild_only()
    @commands.group(
        invoke_without_command=True,
        case_insensitive=True
    )
    async def rps(
        self,
        ctx: commands.Context,
        arg
    ) -> None:
        """
        Play the classic game of Rock Paper Scisorr with your own sir lancebot!
        """
        await self._play_game(ctx, arg)


def setup(bot: Bot) -> None:
    bot.add_cog(RPS(bot))

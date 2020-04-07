import asyncio
import typing as t

import discord
from discord.ext.commands import Cog, Context

from bot.bot import SeasonalBot
from bot.constants import Emojis

CONFIRMATION_MESSAGE = (
    "{opponent}, {requester} want to play Tic-Tac-Toe against you. React to this message with "
    f"{Emojis.confirmation} to accept or with {Emojis.decline} to decline."
)


class Player:
    """Class that contains information about player and functions that interact with player."""

    def __init__(self, user: discord.User, ctx: Context):
        self.user = user
        self.ctx = ctx


class Game:
    """Class that contains information and functions about Tic Tac Toe game."""

    def __init__(self, channel: discord.TextChannel, players: t.List[Player], ctx: Context):
        self.channel = channel
        self.players = players
        self.ctx = ctx

        self.current = self.players[0]
        self.next = self.players[1]

        self.winner: t.Optional[Player] = None
        self.loser: t.Optional[Player] = None

    async def get_confirmation(self) -> t.Tuple[bool, t.Optional[str]]:
        """Ask does user want to play TicTacToe against requester. First player is always requester."""
        confirm_message = await self.ctx.send(
            CONFIRMATION_MESSAGE.format(
                opponent=self.players[1].user.mention,
                requester=self.players[0].user.mention
            )
        )
        await confirm_message.add_reaction(Emojis.confirmation)
        await confirm_message.add_reaction(Emojis.decline)

        def confirm_check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                reaction.emoji in (Emojis.confirmation, Emojis.decline)
                and reaction.message.id == confirm_message.id
                and user == self.players[1].user
            )

        try:
            reaction, user = await self.ctx.bot.wait_for(
                "reaction_add",
                timeout=60.0,
                check=confirm_check
            )
        except asyncio.TimeoutError:
            await confirm_message.delete()
            return False, "Running out of time... Cancelled game."

        await confirm_message.delete()
        if reaction.emoji == Emojis.confirmation:
            return True, None
        else:
            return False, "User declined"


class TicTacToe(Cog):
    """TicTacToe cog contains tic-tac-toe game commands."""

    def __init__(self, bot: SeasonalBot):
        self.bot = bot


def setup(bot: SeasonalBot) -> None:
    """Load TicTacToe Cog."""
    bot.add_cog(TicTacToe(bot))

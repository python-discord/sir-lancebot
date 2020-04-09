import asyncio
import typing as t

import discord
from discord.ext.commands import Cog, Context, check, command, guild_only

from bot.bot import SeasonalBot
from bot.constants import Emojis

CONFIRMATION_MESSAGE = (
    "{opponent}, {requester} want to play Tic-Tac-Toe against you. React to this message with "
    f"{Emojis.confirmation} to accept or with {Emojis.decline} to decline."
)


class Player:
    """Class that contains information about player and functions that interact with player."""

    def __init__(self, user: discord.User, ctx: Context, symbol: str):
        self.user = user
        self.ctx = ctx
        self.symbol = symbol

    async def get_move(self, board: t.Dict[int, str], msg: discord.Message) -> t.Tuple[bool, t.Optional[int]]:
        """
        Get move from user.

        Return is timeout reached and position of field what user will fill when timeout don't reach.
        """
        def check_for_move(r: discord.Reaction, u: discord.User) -> bool:
            return (
                u.id == self.user.id
                and msg.id == r.message.id
                and r.emoji in board.values()
                and r.emoji in Emojis.number_emojis.values()
            )

        try:
            react, _ = await self.ctx.bot.wait_for('reaction_add', timeout=120.0, check=check_for_move)
        except asyncio.TimeoutError:
            return True, None
        else:
            return False, list(Emojis.number_emojis.keys())[list(Emojis.number_emojis.values()).index(react.emoji)]


class Game:
    """Class that contains information and functions about Tic Tac Toe game."""

    def __init__(self, channel: discord.TextChannel, players: t.List[Player], ctx: Context):
        self.channel = channel
        self.players = players
        self.ctx = ctx
        self.board = {
            1: Emojis.number_emojis[1],
            2: Emojis.number_emojis[2],
            3: Emojis.number_emojis[3],
            4: Emojis.number_emojis[4],
            5: Emojis.number_emojis[5],
            6: Emojis.number_emojis[6],
            7: Emojis.number_emojis[7],
            8: Emojis.number_emojis[8],
            9: Emojis.number_emojis[9]
        }

        self.current = self.players[0]
        self.next = self.players[1]

        self.winner: t.Optional[Player] = None
        self.loser: t.Optional[Player] = None
        self.over = False

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
            self.over = True
            await confirm_message.delete()
            return False, "Running out of time... Cancelled game."

        await confirm_message.delete()
        if reaction.emoji == Emojis.confirmation:
            return True, None
        else:
            self.over = True
            return False, "User declined"

    async def add_reactions(self, msg: discord.Message) -> None:
        """Add number emojis to message."""
        for nr in Emojis.number_emojis.values():
            await msg.add_reaction(nr)

    async def send_board(self) -> discord.Message:
        """Send board and return it's message."""
        msg = ""
        c = 0
        for line in self.board.values():
            msg += f"{line} "
            c += 1
            if c == 3:
                msg += "\n"
                c = 0
        return await self.ctx.send(msg)

    async def edit_board(self, message: discord.Message) -> None:
        """Edit Tic Tac Toe game board in message."""
        msg = ""
        c = 0
        for line in self.board.values():
            msg += f"{line} "
            c += 1
            if c == 3:
                msg += "\n"
                c = 0
        await message.edit(content=msg)

    async def play(self) -> None:
        """Start and handle game."""
        await self.ctx.send("It's time for game! Let's begin.")
        board = await self.send_board()
        await self.add_reactions(board)

        for _ in range(9):
            announce = await self.ctx.send(f"{self.current.user.mention}, your turn! React to emoji to mark field.")
            timeout, pos = await self.current.get_move(self.board, board)
            await announce.delete()
            if timeout:
                await self.ctx.send(f"{self.current.user.mention} ran out of time. Canceling game.")
                self.over = True
                return
            self.board[pos] = self.current.symbol
            await self.edit_board(board)
            await board.clear_reaction(Emojis.number_emojis[pos])
            self.current, self.next = self.next, self.current
        self.over = True


def is_channel_free() -> t.Callable:
    """Check is channel where command will be invoked free."""
    async def predicate(ctx: Context) -> bool:
        return all(game.channel != ctx.channel for game in ctx.cog.games if not game.over)
    return check(predicate)


def is_requester_free() -> t.Callable:
    """Check is requester not already in any game."""
    async def predicate(ctx: Context) -> bool:
        return all(
            ctx.author not in (player.user for player in game.players) for game in ctx.cog.games if not game.over
        )
    return check(predicate)


class TicTacToe(Cog):
    """TicTacToe cog contains tic-tac-toe game commands."""

    def __init__(self, bot: SeasonalBot):
        self.bot = bot
        self.games: t.List[Game] = []

    @guild_only()
    @is_channel_free()
    @is_requester_free()
    @command(name="tictactoe", aliases=("ttt",))
    async def tic_tac_toe(self, ctx: Context, opponent: discord.User) -> None:
        """Tic Tac Toe game. Play agains friends. Use reactions to add your mark to field."""
        if not all(
            opponent not in (player.user for player in g.players) for g in ctx.cog.games if not g.over
        ):
            await ctx.send("Opponent is already in game.")
            return
        game = Game(
            ctx.channel,
            [Player(ctx.author, ctx, Emojis.x), Player(opponent, ctx, Emojis.o)],
            ctx
        )
        self.games.append(game)
        confirmed, msg = await game.get_confirmation()

        if not confirmed:
            if msg:
                await ctx.send(msg)
            return
        await game.play()


def setup(bot: SeasonalBot) -> None:
    """Load TicTacToe Cog."""
    bot.add_cog(TicTacToe(bot))
